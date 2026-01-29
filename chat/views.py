import os
import io
import logging
import time
import cloudinary           # Cloudinary Import
import cloudinary.uploader  # Cloudinary Uploader
from django.core.files.base import ContentFile
from google import genai
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatSession, Message, Document
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .rag import ingest_document, retrieve_context, extract_text_from_pdf, delete_document_vectors
from .model_fallback import generate_with_fallback, get_model_display_name, check_service_availability, ModelExhaustionError
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse

load_dotenv()
logger = logging.getLogger(__name__)

# File upload validation settings
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
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
    
    # Handle HTMX partial updates after first message
    if request.method == "GET" and request.headers.get('HX-Request'):
        hx_target = request.headers.get('HX-Target', '')
        
        if hx_target == 'title':
            # Return just the updated title
            return render(request, 'chat/partials/chat_title.html', {
                'session': current_session,
                'is_admin': user.is_staff
            })
        elif hx_target == 'sidebar':
            # Return just the updated sidebar list
            return render(request, 'chat/partials/sidebar_list.html', {
                'chat_sessions': all_sessions,
                'current_session': current_session,
                'is_admin': user.is_staff
            })

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
            file_size_mb = round(uploaded_file.size / (1024 * 1024), 2)
            max_size_mb = MAX_FILE_SIZE // (1024 * 1024)
            return render(request, 'chat/partials/system_message.html', {
                'content': f"❌ File too large!\n\n📊 File size: {file_size_mb}MB\n📏 Maximum allowed: {max_size_mb}MB\n\n💡 Try compressing the PDF or splitting it into smaller files.",
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
            file_identifier = f"{current_session.id}_{uploaded_file.name}"
            try:
                ingest_document(file_identifier, raw_text)
            except Exception as ingest_error:
                # PRODUCTION FIX: Rollback database if Pinecone fails
                logger.error(f"Pinecone ingestion failed, rolling back document: {ingest_error}")
                doc.delete()
                delete_document_vectors(file_identifier)  # Cleanup partial vectors
                raise
            
            logger.info(f"File uploaded successfully: {uploaded_file.name} for session {current_session.id}")
            
            # Refresh attachments list in sidebar
            session_docs = Document.objects.filter(session=current_session).select_related('session').order_by('-uploaded_at')
            return render(request, 'chat/partials/attachments_list.html', {
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
            # Check if this is the first message (before creating it)
            is_first_message = current_session.messages.count() == 0
            
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
                You are Nexus, analyzing the following documents: {doc_names}.
                
                STRICT RULES:
                1. Use the CONTEXT below to answer the user's question.
                2. If the answer is found in the context, explicitly mention it is from the document.
                3. If the answer is NOT in the context, use your general knowledge but mention that the document does not contain this info.
                
                CONTEXT:
                {context}
                """
            else:
                # --- GENERAL MODE (No docs) ---
                system_instruction = """
                You are Nexus, a helpful and intelligent assistant. 
                Engage in normal conversation, answer questions, and assist the user.
                """

            # Generate Response with automatic fallback (BEFORE saving to DB)
            prompt = f"""
            {system_instruction}
            
            USER QUESTION: {user_message}
            """
            
            # Use multi-model fallback system - this will raise exception if it fails
            ai_text, model_used = generate_with_fallback(prompt, system_instruction="")
            
            # IMPORTANT: Only save to database AFTER successful AI response
            # This prevents "ghost messages" (user messages without AI replies) when errors occur
            
            # Save User Message
            user_msg = Message.objects.create(session=current_session, role='user', content=user_message)
            
            # Save assistant response with metadata about which model was used
            assistant_message = Message.objects.create(
                session=current_session, 
                role='assistant', 
                content=ai_text,
                model_used=model_used
            )
            
            # Rename Session if it's the first message
            if current_session.title == "New Conversation":
                # Generate a short title (First 30 chars)
                current_session.title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                current_session.save()

            # Update timestamp so this chat moves to top of list
            current_session.save()
            
            # Store model info in session for UI display
            request.session[f'model_used_{assistant_message.id}'] = model_used
            
            logger.info(f"Chat message processed for session {current_session.id} using {model_used}")
            rendered_html = assistant_message.get_html_content()
            
            # Build response with HTMX headers for first message
            response = render(request, 'chat/partials/message.html', {
                'message': {'content': user_message},
                'response_html': mark_safe(rendered_html),
                'model_used': get_model_display_name(model_used)
            })
            
            # If this was the first message, trigger UI updates
            if is_first_message:
                # Trigger updates for title, sidebar, and URL
                response['HX-Trigger'] = 'firstMessageSent'
                # Also push new URL to browser
                response['HX-Push-Url'] = f'/chat/{current_session.id}/'
            
            return response
            
        except ModelExhaustionError as e:
            # All models exhausted - disable chat interface
            logger.error(f"All models exhausted: {e}")
            return render(request, 'chat/partials/system_message.html', {
                'content': str(e),
                'error': True,
                'disable_chat': True
            })
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Chat message processing failed: {e}")
            
            # Provide specific error messages based on error type
            if 'api_key' in error_str.lower() or 'authentication' in error_str.lower():
                error_message = "❌ API authentication error. Please contact the administrator."
            else:
                error_message = "❌ Failed to generate response. Please try again."
            
            return render(request, 'chat/partials/system_message.html', {
                'content': error_message,
                'error': True
            })

    # 5. Load History - Optimized query
    messages = Message.objects.filter(session=current_session).select_related('session').order_by('created_at')
    
    return render(request, 'chat/index.html', {
        'current_session': current_session,
        'chat_sessions': all_sessions,
        'documents': session_docs, # Only show docs for this chat
        'messages': messages,
        'is_admin': user.is_staff  # Pass admin status to template
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
        
        # Prevent renaming empty conversations (defensive check)
        message_count = session.messages.count()
        if message_count == 0:
            return HttpResponse(status=204)  # No content, just ignore the request
        
        new_title = request.POST.get('new_title')
        if new_title:
            # Trim leading/trailing whitespace and normalize multiple spaces
            new_title = new_title.strip()
            # Remove multiple consecutive spaces
            new_title = ' '.join(new_title.split())
            
            if new_title:  # Ensure it's not empty after trimming
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
@staff_member_required
def delete_chat_session(request, session_id):
    if request.method == "POST":
        session = get_object_or_404(ChatSession, id=session_id)
        session.delete()
        return HttpResponse(status=200)

@login_required
def delete_user_chat_session(request, session_id):
    """Allow users to delete their own chat sessions"""
    if request.method == "POST":
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        # Prevent deletion of empty conversations (defensive check)
        message_count = session.messages.count()
        if message_count == 0:
            return HttpResponse(status=204)  # No content, just ignore the request
        
        session.delete()
        logger.info(f"User {request.user.id} deleted chat session {session_id}")
        # For HTMX requests, return a client-side redirect to root (not /chat/)
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Redirect': '/'})
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


@login_required
def check_availability(request):
    """API endpoint to check if AI service is available"""
    is_available, message = check_service_availability()
    return JsonResponse({
        'available': is_available,
        'message': message
    })