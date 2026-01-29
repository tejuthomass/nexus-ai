#!/bin/bash
set -e

echo "🔨 Building Nexus AI..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Create cache table (required for DatabaseCache)
echo "🗄️ Creating cache table..."
python manage.py createcachetable

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate

echo "✅ Build complete!"
