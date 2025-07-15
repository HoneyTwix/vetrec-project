#!/usr/bin/env python3
"""
Setup script for VetRec Medical Action Extraction System
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd, capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def setup_backend():
    """Set up the backend"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Create .env file if it doesn't exist
    env_file = backend_dir / ".env"
    if not env_file.exists():
        env_example = backend_dir / "env.example"
        if env_example.exists():
            run_command(f"cp env.example .env", cwd=backend_dir)
            print("📝 Created .env file - please edit it with your API keys")
        else:
            print("⚠️  No env.example found - please create .env manually")
    
    return True

def setup_frontend():
    """Set up the frontend"""
    print("\n🎨 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install Node.js dependencies
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    return True

def create_env_files():
    """Create environment files with instructions"""
    print("\n📝 Creating environment files...")
    
    # Backend .env
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        with open(backend_env, "w") as f:
            f.write("""# VetRec Backend Environment Variables
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/vetrec
# For development, you can use SQLite instead:
# DATABASE_URL=sqlite:///./vetrec.db
""")
        print("✓ Created backend/.env")
    
    # Frontend .env.local
    frontend_env = Path("frontend/.env.local")
    if not frontend_env.exists():
        with open(frontend_env, "w") as f:
            f.write("""# VetRec Frontend Environment Variables
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
""")
        print("✓ Created frontend/.env.local")

def main():
    """Main setup function"""
    print("🚀 VetRec Medical Action Extraction System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Set up frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Create environment files
    create_env_files()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit backend/.env with your OpenAI API key")
    print("2. Start the backend: cd backend && python main.py")
    print("3. Start the frontend: cd frontend && npm run dev")
    print("4. Open http://localhost:3000 in your browser")
    print("\nFor Docker deployment:")
    print("cd backend/docker && docker-compose up -d")

if __name__ == "__main__":
    main() 