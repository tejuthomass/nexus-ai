# Nexus

A production-ready RAG (Retrieval-Augmented Generation) chat application built with Django. Upload documents, ask questions, and receive intelligent responses powered by Google Gemini AI with vector-based semantic search.

## Features

- **Hybrid Intelligence** — Automatically switches between general chat and document-based RAG mode
- **Document Analysis** — Upload PDFs and query their contents with semantic search
- **Session-Based Context** — Each conversation maintains its own document collection
- **Multi-Model Fallback** — Automatic failover through 12 AI models for high availability
- **Rate Limiting** — Three-tier system (per-minute, hourly, global) for resource management
- **Admin Dashboard** — User management, chat history monitoring, and system oversight
- **Cloud Storage** — PDF files stored in Cloudinary with automatic cleanup
- **Vector Search** — Pinecone-powered semantic search with optimized 800-char chunking

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Django 5.2 |
| Frontend | HTMX, Tailwind CSS |
| AI | Google Gemini 2.0 Flash |
| Vector DB | Pinecone |
| Database | PostgreSQL (Neon) |
| Storage | Cloudinary |
| Server | Gunicorn |

## Project Structure

```
nexus/
├── chat/                    # Main application
│   ├── models.py            # ChatSession, Message, Document
│   ├── views.py             # Request handlers
│   ├── rag.py               # RAG pipeline (embed, ingest, retrieve)
│   ├── model_fallback.py    # Multi-model fallback system
│   ├── middleware.py        # Rate limiting
│   ├── signals.py           # Cleanup handlers
│   └── templates/           # HTML templates
├── config/                  # Django configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                  # CSS and JavaScript
├── templates/               # Global templates (404, 500)
├── requirements.txt         # Python dependencies
├── Procfile                 # Render/Heroku process config
├── build.sh                 # Build script
└── gunicorn.conf.py         # Production server config
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Comma-separated list of domains |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google AI API key |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX_NAME` | Pinecone index name (default: `nexus-index`) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `ADMIN_URL_PATH` | Custom admin URL path (optional) |

## Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL
- API keys for Gemini, Pinecone, and Cloudinary

### Setup

```bash
# Clone repository
git clone https://github.com/tejuthomass/nexus.git
cd nexus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python manage.py migrate
python manage.py createcachetable

# Create admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Access at `http://127.0.0.1:8000`

### Pinecone Index Setup

Create an index with:
- **Name:** `nexus-index`
- **Dimensions:** 768
- **Metric:** cosine

## Production Deployment (Render)

### Required Files

The repository includes all necessary deployment files:

- `Procfile` — Defines release and web processes
- `build.sh` — Installs dependencies, collects static files, runs migrations
- `runtime.txt` — Specifies Python version (3.11.9)
- `gunicorn.conf.py` — Production server configuration

### Render Configuration

1. **Create Web Service** on Render connected to this repository

2. **Build Command:**
   ```
   ./build.sh
   ```

3. **Start Command:**
   ```
   gunicorn config.wsgi:application
   ```

4. **Environment Variables:** Add all variables from `.env.example`

5. **Database:** Create a PostgreSQL instance on Neon or use Render's managed PostgreSQL

### Environment Variables for Render

Set these in the Render dashboard:

```
SECRET_KEY=<generate-new-key>
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=<your-neon-or-render-postgres-url>
GEMINI_API_KEY=<your-key>
PINECONE_API_KEY=<your-key>
PINECONE_INDEX_NAME=nexus-index
CLOUDINARY_CLOUD_NAME=<your-cloud>
CLOUDINARY_API_KEY=<your-key>
CLOUDINARY_API_SECRET=<your-secret>
```

Generate a new secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## API Rate Limits

The application implements three-tier rate limiting:

| Limit | Value | Scope |
|-------|-------|-------|
| Per-minute | 10 requests | Per user |
| Hourly | 100 requests | Per user |
| Global | 50 parallel | System-wide |

## Model Fallback Hierarchy

When rate limits are hit, the system cascades through:

1. gemini-3-flash-preview
2. gemini-flash-latest
3. gemini-2.5-flash
4. gemini-2.0-flash
5. gemini-flash-lite-latest
6. gemini-2.5-flash-lite
7. gemini-2.0-flash-lite
8. gemma-3-27b → gemma-3-1b

## Security

- All credentials stored in environment variables
- `.env` excluded from version control
- CSRF protection enabled
- Rate limiting prevents abuse
- Session-based document isolation
- Customizable admin URL path

## License

MIT License

---

**Repository:** [github.com/tejuthomass/nexus](https://github.com/tejuthomass/nexus)