import os
import io
import logging
import cloudinary           # Cloudinary Import
import cloudinary.uploader  # Cloudinary Uploader
from django.core.files.base import ContentFile
from google import genai
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatSession, Message, Document
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .rag import ingest_document, retrieve_context, extract_text_from_pdf
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponse

load_dotenv()
logger = logging.getLogger(__name__)

# File upload validation settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.pdf']

@login_required
def chat_view(request, session_id=None):
    user = request.user

    # 1. Logic: Load specific chat OR get the latest one
    if session_id:
        current_session = get_object_or_404(ChatSession, id=session_id, user=user)
    else:
        # Find the most recent session
        current_session = ChatSession.objects.filter(user=user).order_by('-updated_at').first()
        
        # If no session exists at all, create the first one
        if not current_session:
            current_session = ChatSession.objects.create(user=user, title="New Conversation")

    # 2. Sidebar Lists (Only show chats belonging to this user) - Optimized query
    all_sessions = ChatSession.objects.filter(user=user).select_related('user').order_by('-updated_at')
    
    # Show ONLY documents uploaded to THIS session (Privacy)
    session_docs = Document.objects.filter(session=current_session).select_related('session').order_by('-uploaded_at')

    # 3. Handle File Upload
    if request.method == "POST" and request.FILES.get('pdf_file'):
        uploaded_file = request.FILES['pdf_file']
        
        # Validate file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return render(request, 'chat/partials/system_message.html', {
                'content': f"❌ Invalid file type. Only PDF files are allowed.",
                'error': True
            })
        
        # Validate file size
        if uploaded_file.size > MAX_FILE_SIZE:
            return render(request, 'chat/partials/system_message.html', {
                'content': f"❌ File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.",
                'error': True
            })
        
        try:
            # 1. Read file for RAG
            file_content = uploaded_file.read()
            raw_text = extract_text_from_pdf(io.BytesIO(file_content))
            
            # 2. Upload to Cloudinary using the SDK
            # Use a unique public_id to prevent collisions
            unique_public_id = f"session_{current_session.id}_{uploaded_file.name}"
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(file_content), 
                resource_type="auto", 
                public_id=unique_public_id
            )

            # 3. Save reference to Database
            doc = Document(
                session=current_session,
                title=uploaded_file.name
            )
            doc.file.name = upload_result['public_id']
            doc.save()

            # 4. Send to Pinecone
            ingest_document(f"{current_session.id}_{uploaded_file.name}", raw_text)
            
            logger.info(f"File uploaded successfully: {uploaded_file.name} for session {current_session.id}")
            
            # Refresh attachments section
            session_docs = Document.objects.filter(session=current_session).select_related('session').order_by('-uploaded_at')
            return render(request, 'chat/partials/attachments.html', {
                'documents': session_docs
            })
        except ValueError as e:
            logger.error(f"File validation error: {e}")
            return render(request, 'chat/partials/system_message.html', {
                'content': f"❌ {str(e)}",
                'error': True
            })
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return render(request, 'chat/partials/system_message.html', {
                'content': f"❌ Upload failed. Please try again.",
                'error': True
            })

    # 4. Handle Chat Messages
    if request.method == "POST" and request.POST.get('message'):
        user_message = request.POST.get('message', '').strip()
        
        # Validate input
        if not user_message:
            return HttpResponse("Message cannot be empty", status=400)
        
        if len(user_message) > 5000:
            return render(request, 'chat/partials/system_message.html', {
                'content': "❌ Message too long. Maximum 5000 characters.",
                'error': True
            })
        
        try:
            # Save User Message
            Message.objects.create(session=current_session, role='user', content=user_message)
            
            # Rename Session if it's the first message
            if current_session.title == "New Conversation":
                # Generate a short title (First 30 chars)
                current_session.title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                current_session.save()

            # Update timestamp so this chat moves to top of list
            current_session.save() 

            # --- HYBRID INTELLIGENCE LOGIC ---
            has_documents = Document.objects.filter(session=current_session).exists()
            
            system_instruction = ""
            context = ""

            if has_documents:
                # --- RAG MODE (Docs exist) ---
                context = retrieve_context(user_message, session_id=current_session.id)
                
                # Get filenames for citation
                doc_names = ", ".join([d.title for d in session_docs])
                
                system_instruction = f"""
                You are Nexus, an AI assistant analyzing the following documents: {doc_names}.
                
                STRICT RULES:
                1. Use the CONTEXT below to answer the user's question.
                2. If the answer is found in the context, explicitly mention it is from the document.
                3. If the answer is NOT in the context, use your general knowledge but mention that the document does not contain this info.
                
                CONTEXT:
                {context}
                """
            else:
                # --- GENERAL AI MODE (No docs) ---
                system_instruction = """
                You are Nexus, a helpful and intelligent AI assistant. 
                Engage in normal conversation, answer questions, and assist the user.
                """

            # Generate Response
            prompt = f"""
            {system_instruction}
            
            USER QUESTION: {user_message}
            """

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            ai_text = response.text
            
            assistant_message = Message.objects.create(session=current_session, role='assistant', content=ai_text)
            
            logger.info(f"Chat message processed for session {current_session.id}")
            rendered_html = assistant_message.get_html_content()
            return render(request, 'chat/partials/message.html', {
                'message': {'content': user_message},
                'response_html': mark_safe(rendered_html)
            })
        except Exception as e:
            logger.error(f"Chat message processing failed: {e}")
            return render(request, 'chat/partials/system_message.html', {
                'content': "❌ Failed to generate response. Please try again.",
                'error': True
            })

    # 5. Load History - Optimized query
    messages = Message.objects.filter(session=current_session).select_related('session').order_by('created_at')
    
    return render(request, 'chat/index.html', {
        'current_session': current_session,
        'chat_sessions': all_sessions,
        'documents': session_docs, # Only show docs for this chat
        'messages': messages
    })

@login_required
def new_chat(request):
    # Logic: Prevent empty chats
    # Check the user's last session
    last_session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
    
    # If the last session has NO messages, just redirect to it (Don't create a new one)
    if last_session and last_session.messages.count() == 0:
        return redirect('chat_session', session_id=last_session.id)
        
    # Otherwise, create a fresh one
    ChatSession.objects.create(user=request.user, title="New Conversation")
    return redirect('chat')

@login_required
def rename_chat(request, session_id):
    # --- TASK 4: RENAME CHAT LOGIC ---
    if request.method == "POST":
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        new_title = request.POST.get('new_title')
        if new_title:
            session.title = new_title
            session.save()
            
        # Return the new title as simple HTML to swap
        return render(request, 'chat/partials/chat_title.html', {'session': session})

@staff_member_required # <--- Security: Only Admins can enter
def admin_dashboard(request):
    # 1. Get all users (exclude the admin themselves to keep list clean)
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # 2. Get stats for each user
    user_data = []
    for u in users:
        sessions = ChatSession.objects.filter(user=u).order_by('-created_at')
        user_data.append({
            'user': u,
            'session_count': sessions.count(),
            'sessions': sessions
        })

    return render(request, 'chat/dashboard.html', {'user_data': user_data})

@staff_member_required
def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        user.delete() # This cascades and deletes their chats/files too
        return render(request, 'chat/partials/empty.html') # Return nothing (removes element)

@staff_member_required
def delete_chat_session(request, session_id):
    if request.method == "POST":
        session = get_object_or_404(ChatSession, id=session_id)
        session.delete()
        return render(request, 'chat/partials/empty.html')

@login_required
def delete_user_chat_session(request, session_id):
    """Allow users to delete their own chat sessions"""
    if request.method == "POST":
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.delete()
        logger.info(f"User {request.user.id} deleted chat session {session_id}")
        # Redirect to main chat page or create new session
        return redirect('chat')
        
@staff_member_required
def view_chat_readonly(request, session_id):
    # Read-Only view for Admins
    session = get_object_or_404(ChatSession, id=session_id)
    messages = Message.objects.filter(session=session).order_by('created_at')
    return render(request, 'chat/partials/admin_chat_view.html', {
        'session': session,
        'messages': messages
    })

@staff_member_required
def api_admin_chat(request, session_id):
    """API endpoint to get chat data for admin modal"""
    from django.http import JsonResponse
    
    session = get_object_or_404(ChatSession, id=session_id)
    messages = Message.objects.filter(session=session).order_by('created_at')
    documents = Document.objects.filter(session=session).order_by('-uploaded_at')
    
    # Format messages for JSON
    messages_data = []
    for msg in messages:
        messages_data.append({
            'role': msg.role,
            'content': msg.content,
            'html_content': msg.get_html_content() if msg.role == 'assistant' else '',
            'created_at': msg.created_at.isoformat()
        })
    
    # Format documents for JSON
    documents_data = []
    for doc in documents:
        documents_data.append({
            'title': doc.title,
            'file_url': doc.file.url,
            'uploaded_at': doc.uploaded_at.isoformat()
        })
    
    return JsonResponse({
        'id': session.id,
        'title': session.title,
        'user': session.user.username,
        'messages': messages_data,
        'documents': documents_data
    })