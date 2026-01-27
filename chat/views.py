import os
import io
import cloudinary           # Cloudinary Import
import cloudinary.uploader  # Cloudinary Uploader
from django.core.files.base import ContentFile
import markdown
from google import genai
from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatSession, Message, Document
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .rag import ingest_document, retrieve_context, extract_text_from_pdf
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

load_dotenv()

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

    # 2. Sidebar Lists (Only show chats belonging to this user)
    all_sessions = ChatSession.objects.filter(user=user).order_by('-updated_at')
    
    # Show ONLY documents uploaded to THIS session (Privacy)
    session_docs = Document.objects.filter(session=current_session).order_by('-uploaded_at')

    # 3. Handle File Upload
    if request.method == "POST" and request.FILES.get('pdf_file'):
        uploaded_file = request.FILES['pdf_file']
        
        # 1. Read file for RAG (Keep this logic)
        file_content = uploaded_file.read()
        raw_text = extract_text_from_pdf(io.BytesIO(file_content))
        
        # 2. Upload to Cloudinary using the SDK (As per docs)
        # resource_type="auto" allows PDF viewing
        upload_result = cloudinary.uploader.upload(
            io.BytesIO(file_content), 
            resource_type="auto", 
            public_id=uploaded_file.name
        )

        # 3. Save reference to Database
        # We manually link the uploaded Public ID to the Django FileField
        doc = Document(
            session=current_session,
            title=uploaded_file.name
        )
        doc.file.name = upload_result['public_id'] # Link to Cloudinary ID
        doc.save()

        # 4. Send to Pinecone
        ingest_document(f"{current_session.id}_{uploaded_file.name}", raw_text)
        
        return render(request, 'chat/partials/system_message.html', {
            'content': f"✅ Uploaded '{uploaded_file.name}' to Cloud & RAG."
        })

    # 4. Handle Chat Messages
    if request.method == "POST" and request.POST.get('message'):
        user_message = request.POST.get('message')
        
        # Save User Message
        Message.objects.create(session=current_session, role='user', content=user_message)
        
        # Rename Session if it's the first message
        if current_session.title == "New Conversation":
            # Generate a short title (First 30 chars)
            current_session.title = user_message[:30] + "..."
            current_session.save()

        # Update timestamp so this chat moves to top of list
        current_session.save() 

        # --- HYBRID INTELLIGENCE LOGIC (Task 2) ---
        has_documents = Document.objects.filter(session=current_session).exists()
        
        system_instruction = ""
        context = ""

        if has_documents:
            # --- RAG MODE (Docs exist) ---
            # Retrieve context from Pinecone
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
        
        Message.objects.create(session=current_session, role='assistant', content=ai_text)
        
        return render(request, 'chat/partials/message.html', {
            'message': {'content': user_message}, 
            'response': markdown.markdown(ai_text)
        })

    # 5. Load History
    messages = Message.objects.filter(session=current_session).order_by('created_at')
    
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
        
@staff_member_required
def view_chat_readonly(request, session_id):
    # Read-Only view for Admins
    session = get_object_or_404(ChatSession, id=session_id)
    messages = Message.objects.filter(session=session).order_by('created_at')
    return render(request, 'chat/partials/admin_chat_view.html', {
        'session': session,
        'messages': messages
    })