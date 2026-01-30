#!/bin/bash
set -e

echo "🔨 Building Nexus AI..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "📦 Collecting static files..."
# Debug: Show source static directory
echo "📁 Source static files:"
ls -la static/ || echo "No static directory found!"
ls -la static/css/ || echo "No css directory"
ls -la static/js/ || echo "No js directory"

# Clear staticfiles directory first to force fresh collection
rm -rf staticfiles/
mkdir -p staticfiles/
python manage.py collectstatic --noinput --clear -v 2

# Debug: Show what was collected
echo "📁 Static files collected:"
ls -la staticfiles/ || echo "No staticfiles directory"

# Create cache table (required for DatabaseCache)
echo "🗄️ Creating cache table..."
python manage.py createcachetable

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate

# Create superuser from environment variables if not exists
echo "👤 Setting up superuser..."
python manage.py create_superuser_if_missing

echo "✅ Build complete!"
