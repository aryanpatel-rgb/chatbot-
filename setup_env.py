#!/usr/bin/env python3
"""
Setup script for Medical Chatbot Environment
This script helps set up the required environment variables and checks dependencies.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with template"""
    env_path = Path('.env')
    
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    env_template = """# Medical Chatbot Environment Variables
# Copy this file and add your actual API keys

# Pinecone API Key (get from https://www.pinecone.io/)
PINECONE_API_KEY=your_pinecone_api_key_here

# OpenAI API Key (get from https://platform.openai.com/)
OPENAI_API_KEY=your_openai_api_key_here

# Flask Secret Key (generate a secure random key)
FLASK_SECRET_KEY=your_super_secret_flask_key_here

# Optional: Set to production for deployment
FLASK_ENV=development
"""
    
    with open('.env', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env file template")
    print("⚠️  Please edit .env and add your actual API keys")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'langchain',
        'sentence_transformers',
        'pypdf',
        'python-dotenv',
        'pinecone',
        'openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def main():
    """Main setup function"""
    print("🏥 Medical Chatbot Setup Script")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Check dependencies
    print("\nChecking dependencies...")
    check_dependencies()
    
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python store_index.py (to create vector index)")
    print("3. Run: python app.py (to start the chatbot)")
    print("\n🚀 Happy chatting!")

if __name__ == "__main__":
    main()
