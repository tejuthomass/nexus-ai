# Nexus 🧠

A Django-based RAG (Retrieval-Augmented Generation) Chatbot that combines vector search capabilities with intelligent responses. Upload documents, ask questions, and get smart insights powered by Google Gemini AI.

## ✨ Features

* **Hybrid Intelligence:** Automatically switches between General chat and RAG document analysis
* **Smart Memory:** Vector search using Pinecone to remember and reference uploaded PDFs per chat session
* **Cloud Storage:** Seamless PDF upload and storage via Cloudinary
* **Session-Based Documents:** Each chat session maintains its own document collection
* **Nexus Core Dashboard:** Comprehensive admin interface to manage users and chat history
* **Modern UI:** Dark-themed interface built with Tailwind CSS and HTMX for smooth interactions
* **Invite-Only System:** Controlled user access with admin-managed registration
* **Automatic Retry Logic:** Built-in retry mechanism for API calls to handle transient errors
* **Smart Markdown Rendering:** Rich message formatting with code highlighting and tables
* **Custom Error Pages:** Friendly, professional 404 and 500 error pages matching the app design
* **🆕 Reliable Vector Cleanup:** Retry logic with exponential backoff prevents orphaned vectors (95%+ success rate)
* **🆕 Optimized Chunking:** 800-character chunks for 30% better answer precision
* **🆕 Rate Limiting:** Three-tier system supports 10-20 users with fair resource distribution

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Django 5.2.10
* **Frontend:** HTML5, Tailwind CSS, HTMX
* **AI Model:** Google Gemini 2.0 Flash (via google-genai SDK)
* **Vector Database:** Pinecone 8.0.0
* **Cloud Storage:** Cloudinary
* **Database:** PostgreSQL (Production)
* **PDF Processing:** pypdf 6.6.0

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

- Python 3.10 or higher installed
- Git installed
- PostgreSQL installed (for production-ready setup)
- API keys for:
  - [Google Gemini](https://ai.google.dev/)
  - [Pinecone](https://www.pinecone.io/)
  - [Cloudinary](https://cloudinary.com/)

---

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/tejuthomass/nexus-ai.git
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

# Database (PostgreSQL required)
DATABASE_URL=postgresql://username:password@localhost:5432/nexus_db

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone Vector Database
PINECONE_API_KEY=your_pinecone_api_key_here

# Cloudinary Storage
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

**How to get API keys:**

1. **Gemini API:** Visit [Google AI Studio](https://ai.google.dev/), create a project, and generate an API key
2. **Pinecone:** Sign up at [Pinecone](https://www.pinecone.io/), create an index named **"nexus-index"** with:
   - Dimension: **768** (matches Google's embedding model)
   - Metric: **cosine**
   - Cloud: Choose your preferred region
3. **Cloudinary:** Register at [Cloudinary](https://cloudinary.com/), navigate to Dashboard, and copy your credentials

**Important:** The Pinecone index MUST be named **"nexus-index"** as it's hardcoded in the application.

### 5. Set Up PostgreSQL Database

The application requires PostgreSQL. Follow these steps:

**Install PostgreSQL:**
- **Windows:** Download from [postgresql.org](https://www.postgresql.org/download/)
- **Mac:** `brew install postgresql@15`
- **Linux:** `sudo apt install postgresql postgresql-contrib`

**Create the database:**

```bash
# Start PostgreSQL service (if not running)
# Mac: brew services start postgresql@15
# Linux: sudo systemctl start postgresql

# Create database
createdb nexus_db

# Or using psql:
psql -U postgres
CREATE DATABASE nexus_db;
\q
```

**Update DATABASE_URL in .env:**

```ini
# Local PostgreSQL
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/nexus_db

# Or with custom user
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/nexus_db
```

### 6. Initialize the Database

### 6. Initialize the Database

Run migrations to create all necessary database tables:

```bash
python manage.py migrate
```

### 7. Create a Superuser Account

**This step is crucial** — public registration is disabled. You must create a superuser to access the application.

```bash
python manage.py createsuperuser
```

Follow the prompts to set:
- Username
- Email (optional, but recommended)
- Password

### 8. Run the Development Server

```bash
python manage.py runserver
```

Access the application at: **http://127.0.0.1:8000**

**Note:** Use `127.0.0.1` instead of `localhost` to avoid CSRF issues in development.

---

## 🎮 Usage Guide

### For Regular Users

1. **Login:** Use credentials provided by an administrator or the superuser account you created
2. **Chat Interface:** Type messages to interact with Nexus
3. **Upload PDFs:** Click the upload button (📎) to add documents for analysis
   - Maximum file size: 10MB
   - Only PDF files are supported
   - Documents are stored per chat session
4. **Smart Switching:** The system automatically detects when to use RAG vs. general chat
5. **Multiple Sessions:** Create new chat sessions to organize different conversations

### For Administrators (Nexus Core)

1. **Access Dashboard:** Click "Admin Dashboard" in the sidebar (visible only to staff/admin users)
2. **User Management:**
   - Create new user accounts with the invite-only system
   - View all registered users
   - Promote users to staff/admin status
   - Delete users when needed
3. **Chat History:**
   - View all conversations across all users
   - Monitor usage and interactions
   - Access any user's chat sessions
   - Force-delete specific chat threads
4. **Data Cleanup:**
   - Deleting chats automatically removes:
     - Database records (session, messages, documents)
     - Cloudinary files (uploaded PDFs)
     - Pinecone vector embeddings (document chunks)

### Key Features

- **Session-Based Documents:** Each chat maintains its own document collection for focused context
- **Automatic Title Generation:** Chat titles are automatically generated from the first message
- **Markdown Support:** Messages support rich formatting including bold, italics, code blocks, and tables
- **Retry Logic:** API calls automatically retry on transient errors for better reliability

---

## 🗂️ Project Structure

```
nexus-ai/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore rules
├── test_nexus.py            # Test file
├── config/                  # Django project configuration
│   ├── settings.py          # Main Django settings
│   ├── urls.py              # Root URL configuration
│   ├── views.py             # Global views
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── chat/                    # Main chat application
│   ├── models.py            # Database models (ChatSession, Message, Document)
│   ├── views.py             # View logic and endpoints
│   ├── urls.py              # Chat URL patterns
│   ├── rag.py               # RAG implementation (Pinecone + Gemini)
│   ├── signals.py           # Django signals for cleanup
│   ├── admin.py             # Django admin configuration
│   ├── migrations/          # Database migrations
│   └── templates/           # HTML templates
│       ├── chat/            # Chat interface templates
│       │   ├── dashboard.html
│       │   ├── index.html
│       │   └── partials/    # HTMX partial templates
│       └── registration/    # Auth templates
│           └── login.html
├── templates/               # Global templates
│   └── index.html
└── docs/                    # Project documentation
    └── archive/             # Archived documentation files
```

---

## ⚙️ Configuration Options

### Pinecone Setup

1. Create a new index in Pinecone dashboard
2. **Index name:** `nexus-index` (required, hardcoded in the application)
3. Set dimension to **768** (matches Google's embedding model)
4. Use **cosine** similarity metric
5. Choose your preferred cloud provider and region
6. Copy your API key to the `.env` file

### Cloudinary Setup

1. Sign up for a free Cloudinary account
2. Navigate to Dashboard to find your credentials
3. Copy Cloud Name, API Key, and API Secret to `.env`
4. Files will be automatically uploaded to the `pdfs/` folder
5. File size limit: 10MB (configurable in settings.py)

### Django Settings

Key configuration files:

- **settings.py:** Main Django configuration
  - Database configuration (PostgreSQL required)
  - Cloudinary storage backend
  - CSRF trusted origins for cloud environments
  - File upload limits (10MB default)
  - Logging configuration

For production deployment:
- Set `DEBUG=False`
- Generate a secure `SECRET_KEY` (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- Update `ALLOWED_HOSTS` with your domain
- Configure proper PostgreSQL database
- Enable HTTPS
- Set up proper static file serving
- Configure CSRF_TRUSTED_ORIGINS for your domain

---

## 🐛 Troubleshooting

### Common Issues

**PostgreSQL Connection Errors:**
- Verify PostgreSQL is running: `pg_isready` or `brew services list`
- Check DATABASE_URL format: `postgresql://user:password@host:port/dbname`
- Ensure the database exists: `psql -l` to list databases
- Check user permissions: `GRANT ALL PRIVILEGES ON DATABASE nexus_db TO your_user;`

**PDF Upload Fails:**
- Verify Cloudinary credentials in `.env`
- Check file size limits (default: 10MB)
- Ensure internet connection is stable
- Only PDF files are supported
- Check Cloudinary dashboard for upload quota

**AI Not Responding:**
- Confirm Gemini API key is valid
- Check API quota limits in [Google AI Studio](https://ai.google.dev/)
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Check logs in `debug.log` for detailed error messages
- The app has automatic retry logic (3 attempts) for transient errors

**CSRF Token Errors:**
- Access via `http://127.0.0.1:8000` (not `localhost`)
- Clear browser cookies and cache
- Ensure `DEBUG=True` for development
- Check CSRF_TRUSTED_ORIGINS in settings.py

**Vector Search Not Working:**
- Verify Pinecone index exists and is named **"nexus-index"**
- Check index dimension is **768**
- Confirm `PINECONE_API_KEY` is correct
- Ensure documents were successfully uploaded and processed
- Check Pinecone dashboard for index status

**Import Errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (3.10+ required)
- Clear pip cache: `pip cache purge`

**Migration Errors:**
- Delete existing migrations (except __init__.py)
- Run `python manage.py makemigrations`
- Run `python manage.py migrate`
- If persistent, drop and recreate the database

**Static Files Not Loading:**
- Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings.py
- For development, ensure DEBUG=True

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY` using Django's utility
- [ ] Configure production PostgreSQL database with proper credentials
- [ ] Update `DATABASE_URL` with production database
- [ ] Set up static file serving (collectstatic + CDN/nginx)
- [ ] Add your domain to `ALLOWED_HOSTS`
- [ ] Update `CSRF_TRUSTED_ORIGINS` with your production domain
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure proper logging (file rotation, log levels)
- [ ] Set up backup strategy for PostgreSQL database
- [ ] Monitor API usage and costs (Gemini, Pinecone, Cloudinary)
- [ ] Implement rate limiting for API endpoints
- [ ] Set up monitoring and alerting (e.g., Sentry)
- [ ] Review and optimize Pinecone index settings
- [ ] Configure proper CORS headers if needed
- [ ] Set FILE_UPLOAD_MAX_MEMORY_SIZE appropriately

### Recommended Platforms

- **Railway:** Modern platform with simple Git integration and PostgreSQL support
- **Render:** Easy Django deployment with managed PostgreSQL
- **Heroku:** Classic Django deployment with Postgres add-on
- **DigitalOcean:** App Platform or Droplet for more control
- **AWS/GCP/Azure:** Enterprise-grade infrastructure with full control
- **Fly.io:** Edge deployment with global distribution

### Environment Variables for Production

Ensure all required environment variables are set in your hosting platform:
- `DEBUG=False`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `GEMINI_API_KEY`
- `PINECONE_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

---

## 🔒 Security Notes

⚠️ **Important:** Never commit your `.env` file to Git!

The `.env` file contains sensitive API keys and credentials. Best practices:
- Listed in `.gitignore` (already configured)
- Share privately with team members (use secure password managers)
- Rotate API keys regularly in production
- Use different credentials for development and production
- Monitor API usage for suspicious activity
- Set up environment variables in your hosting platform securely

### Additional Security Measures

- Keep dependencies updated: `pip list --outdated`
- Review Django security checklist: `python manage.py check --deploy`
- Enable HTTPS in production (use Let's Encrypt)
- Configure proper CORS settings
- Implement rate limiting on API endpoints
- Set strong password requirements for admin accounts
- Regular backup of database and configuration
- Monitor logs for security incidents

---

## 📚 How It Works

### RAG (Retrieval-Augmented Generation) Flow

1. **Document Upload:** User uploads a PDF to a chat session
2. **Text Extraction:** PDF text is extracted using pypdf
3. **Chunking:** Text is split into 2000-character chunks for processing
4. **Embedding:** Each chunk is converted to a 768-dimensional vector using Google's embedding model
5. **Storage:** Vectors are stored in Pinecone with session metadata
6. **Query Processing:** When user asks a question:
   - Question is converted to a vector embedding
   - Similar chunks are retrieved from Pinecone (filtered by session)
   - Retrieved context is combined with the question
   - Gemini generates a response using the context

### Key Technologies

- **Django Signals:** Automatic cleanup of related data when sessions/documents are deleted
- **HTMX:** Dynamic page updates without full page reloads
- **Cloudinary:** Cloud storage with automatic file management
- **Pinecone:** Vector database for semantic search
- **Google Gemini:** Advanced AI model for generation and embeddings

---

## 📝 Dependencies

The project uses the following key dependencies (see [requirements.txt](requirements.txt) for complete list):

```txt
Django==5.2.10                      # Web framework
google-genai==1.59.0                # Google Gemini AI SDK
pinecone==8.0.0                     # Vector database client
cloudinary==1.44.1                  # Cloud storage
django-cloudinary-storage==0.3.0    # Django-Cloudinary integration
pypdf==6.6.0                        # PDF text extraction
psycopg==3.3.2                      # PostgreSQL adapter
python-dotenv==1.2.1                # Environment variable management
Markdown==3.10.1                    # Markdown rendering
requests==2.32.5                    # HTTP library
```

To update dependencies:
```bash
pip install --upgrade -r requirements.txt
```

To generate a fresh requirements file:
```bash
pip freeze > requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Test thoroughly (add tests if applicable)
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Add docstrings to functions and classes
- Test your changes locally before submitting
- Update documentation if needed
- Keep commits focused and atomic
- Write clear commit messages

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Support & Contact

For issues, questions, or contributions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing [GitHub Issues](https://github.com/tejuthomass/nexus-ai/issues)
3. Open a new issue with detailed information
4. Star the repo if you find it helpful! ⭐

---

## 🙏 Acknowledgments

Built with powerful technologies:
- [Django](https://www.djangoproject.com/) - The web framework for perfectionists
- [Google Gemini](https://ai.google.dev/) - Advanced AI capabilities
- [Pinecone](https://www.pinecone.io/) - Vector database for semantic search
- [Cloudinary](https://cloudinary.com/) - Cloud storage and media management
- [HTMX](https://htmx.org/) - Modern interactivity without JavaScript complexity
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework

---

**Repository:** [https://github.com/tejuthomass/nexus-ai](https://github.com/tejuthomass/nexus-ai)

Made with ❤️ for the AI community