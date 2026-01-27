# Nexus AI 🧠

A Django-based RAG (Retrieval-Augmented Generation) Chatbot that combines Google Gemini AI with vector search capabilities. Upload documents, ask questions, and get intelligent responses powered by cutting-edge AI technology.

## ✨ Features

* **Hybrid Intelligence:** Automatically switches between General AI chat and RAG document analysis
* **Smart Memory:** Vector search using Pinecone to remember and reference uploaded PDFs
* **Cloud Storage:** Seamless PDF upload and storage via Cloudinary
* **Nexus Core Dashboard:** Comprehensive admin interface to manage users and chat history
* **Modern UI:** Dark-themed interface built with Tailwind CSS and HTMX for smooth interactions
* **Invite-Only System:** Controlled user access with admin-managed registration

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Django 5
* **Frontend:** HTML5, Tailwind CSS, HTMX
* **AI Model:** Google Gemini 2.5 Flash
* **Vector Database:** Pinecone
* **Cloud Storage:** Cloudinary
* **Database:** SQLite (Development) / PostgreSQL (Production)

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

- Python 3.10 or higher installed
- Git installed
- API keys for:
  - [Google Gemini](https://ai.google.dev/)
  - [Pinecone](https://www.pinecone.io/)
  - [Cloudinary](https://cloudinary.com/)

---

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone <YOUR_REPO_URL_HERE>
cd nexus-ai
```

### 2. Set Up Virtual Environment

It is **strongly recommended** to use a virtual environment to manage dependencies.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a file named `.env` in the root directory (same folder as `manage.py`).

**Template for `.env`:**

```ini
# Django Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=127.0.0.1,localhost

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone Vector Database
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENV=us-east-1

# Cloudinary Storage
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

**How to get API keys:**

1. **Gemini API:** Visit [Google AI Studio](https://ai.google.dev/), create a project, and generate an API key
2. **Pinecone:** Sign up at [Pinecone](https://www.pinecone.io/), create an index, and copy your API key
3. **Cloudinary:** Register at [Cloudinary](https://cloudinary.com/), navigate to Dashboard, and copy your credentials

### 5. Initialize the Database

```bash
python manage.py migrate
```

### 6. Create a Superuser Account

**This step is crucial** — public registration is disabled. You must create a superuser to access the application.

```bash
python manage.py createsuperuser
```

Follow the prompts to set:
- Username
- Email (optional)
- Password

### 7. Run the Development Server

```bash
python manage.py runserver
```

Access the application at: **http://127.0.0.1:8000**

---

## 🎮 Usage Guide

### For Regular Users

1. **Login:** Use credentials provided by an administrator
2. **Chat Interface:** Type messages to interact with the AI
3. **Upload PDFs:** Click the upload button to add documents for analysis
4. **Smart Switching:** The system automatically detects when to use RAG vs. general chat

### For Administrators (Nexus Core)

1. **Access Dashboard:** Click "Admin Dashboard" in the sidebar
2. **User Management:**
   - Create new user accounts (invite-only system)
   - View all registered users
   - Delete users when needed
3. **Chat History:**
   - View all conversations across users
   - Monitor AI usage and interactions
   - Force-delete specific chat threads
4. **Data Cleanup:**
   - Deleting chats automatically removes:
     - Database records
     - Cloudinary files
     - Pinecone vector embeddings

---

## 🗂️ Project Structure

```
nexus-ai/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── db.sqlite3               # SQLite database (auto-generated)
├── nexus/                   # Main Django app
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI configuration
├── chat/                    # Chat application
│   ├── models.py            # Database models
│   ├── views.py             # View logic
│   ├── urls.py              # Chat URL patterns
│   └── templates/           # HTML templates
└── static/                  # Static files (CSS, JS)
```

---

## ⚙️ Configuration Options

### Pinecone Setup

1. Create a new index in Pinecone dashboard
2. Set dimension to **768** (matches the embedding model)
3. Use **cosine** similarity metric
4. Copy your environment (e.g., `us-east-1`)

### Cloudinary Setup

1. Create a folder structure for organizing PDFs (optional)
2. Enable unsigned uploads if needed
3. Set upload presets in dashboard

### Django Settings

For production deployment, ensure you:
- Set `DEBUG=False`
- Generate a secure `SECRET_KEY`
- Update `ALLOWED_HOSTS` with your domain
- Configure PostgreSQL instead of SQLite
- Enable HTTPS

---

## 🐛 Troubleshooting

### Common Issues

**PDF Upload Fails:**
- Verify Cloudinary credentials in `.env`
- Check file size limits (default: 10MB)
- Ensure internet connection is stable

**AI Not Responding:**
- Confirm Gemini API key is valid
- Check API quota limits in Google Cloud Console
- Verify `GEMINI_API_KEY` is set correctly

**CSRF Token Errors:**
- Access via `http://127.0.0.1:8000` (not `localhost`)
- Clear browser cookies and cache
- Ensure `DEBUG=True` for development

**Vector Search Not Working:**
- Verify Pinecone index exists
- Check index dimension is **768**
- Confirm `PINECONE_ENV` matches your region

**Import Errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version (3.10+ required)

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up static file serving
- [ ] Enable HTTPS
- [ ] Configure CORS if using separate frontend
- [ ] Set up backup strategy for database
- [ ] Monitor API usage and costs
- [ ] Implement rate limiting

### Recommended Platforms

- **Heroku:** Easy Django deployment with Postgres add-on
- **Railway:** Modern platform with simple Git integration
- **DigitalOcean:** App Platform or Droplet for more control
- **AWS/GCP/Azure:** Enterprise-grade infrastructure

---

## 🔒 Security Notes

⚠️ **Important:** Never commit your `.env` file to Git!

The `.env` file contains sensitive API keys. It should be:
- Listed in `.gitignore`
- Shared privately with team members
- Stored securely (use a password manager)
- Rotated regularly in production

---

## 📝 Requirements.txt

If you don't have a `requirements.txt` file yet, create one with:

```txt
Django==5.0
python-decouple==3.8
google-generativeai==0.3.1
pinecone-client==3.0.0
cloudinary==1.36.0
PyPDF2==3.0.1
langchain==0.1.0
```

Generate automatically with: `pip freeze > requirements.txt`

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Support

For issues or questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Contact the maintainers

---

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- Pinecone for vector search
- Cloudinary for file storage
- Django community for the robust framework

---

**Made with ❤️ by [Your Name]**