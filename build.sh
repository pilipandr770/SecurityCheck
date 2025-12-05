#!/bin/bash
# Build script for Render

# Install Python dependencies
pip install -r requirements.txt

# Create database tables
cd backend
python -c "from app import app, db; 
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')"

echo "Build completed successfully!"
