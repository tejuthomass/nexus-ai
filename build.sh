#!/bin/bash
set -e

echo "🔨 Building Nexus..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "📦 Collecting static files..."
# Debug: Show source static directory
echo "📁 Source static files:"
ls -la static/ || echo "No static directory found!"
ls -la static/css/ || echo "No css directory"
ls -la static/js/ || echo "No js directory"

# Clear and collect static files fresh (including Django admin static files)
rm -rf staticfiles/
python manage.py collectstatic --noinput --clear

# Debug: Show what was collected
echo "📁 Static files collected:"
ls -la staticfiles/ || echo "No staticfiles directory"
ls -la staticfiles/admin/ || echo "No admin static files"
ls -la staticfiles/css/ || echo "No css directory in staticfiles"
ls -la staticfiles/js/ || echo "No js directory in staticfiles"

# Run migrations first (required before createcachetable)
echo "🔄 Running migrations..."
python manage.py migrate

# Create cache table (required for DatabaseCache)
# This must run AFTER migrate so Django's database tables exist
echo "🗄️ Creating cache table..."
python manage.py createcachetable || echo "Cache table already exists or could not be created"

# Create superuser from environment variables if not exists
echo "👤 Setting up superuser..."
python manage.py create_superuser_if_missing

echo "✅ Build complete!"
