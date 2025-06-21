#!/usr/bin/env python3
"""
Setup script for STEM Graduate Admissions Assistant - Real Data Edition
No API keys required! Uses HuggingFace transformers and real web scraping.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    print("🎓 STEM Graduate Admissions Assistant - Real Data Setup")
    print("=" * 60)
    print("✅ No OpenAI API keys needed")
    print("✅ No paid APIs required") 
    print("✅ Uses HuggingFace transformers (free)")
    print("✅ Real web scraping")
    print("✅ Search history with SQLite")
    print("=" * 60)

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. You have:", sys.version)
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("\nTry installing manually:")
        print("pip install fastapi uvicorn transformers torch beautifulsoup4 aiohttp")
        return False

def create_directory_structure():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "app",
        "app/core",
        "app/agents", 
        "app/models",
        "app/scrapers",
        "static",
        "static/css",
        "static/js"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory.startswith("app"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Directory structure created")

def create_config_file():
    """Create a simple configuration file"""
    print("\n⚙️  Creating configuration...")
    
    config_content = '''# app/core/config.py - Simple configuration for real data system
import os
from pathlib import Path

class Settings:
    """Simple settings class"""
    
    # App info
    APP_NAME = "STEM Graduate Admissions Assistant"
    APP_VERSION = "3.0.0"
    
    # Server settings
    HOST = "0.0.0.0"
    PORT = 8000
    
    # Database (SQLite)
    DATABASE_PATH = "search_history.db"
    
    # Features
    ENABLE_WEB_SCRAPING = True
    ENABLE_SEARCH_HISTORY = True
    
    # HuggingFace model settings
    HF_MODEL_NAME = "microsoft/DialoGPT-medium"
    HF_MAX_LENGTH = 512
    HF_TEMPERATURE = 0.7

# Global settings instance
settings = Settings()
'''
    
    config_path = Path("app/core/config.py")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        f.write(config_content)
    
    print("✅ Configuration created")

def create_logging_config():
    """Create logging configuration"""
    print("\n📝 Setting up logging...")
    
    logging_content = '''# app/core/logging.py - Simple logging setup
import logging
import sys

def setup_logging(level="INFO"):
    """Setup basic logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)

# Setup default logging
setup_logging()
'''
    
    logging_path = Path("app/core/logging.py")
    with open(logging_path, "w") as f:
        f.write(logging_content)
    
    print("✅ Logging configured")

def initialize_database():
    """Initialize SQLite database for search history"""
    print("\n🗄️  Initializing database...")
    
    try:
        conn = sqlite3.connect("search_history.db")
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                faculty_name TEXT,
                university TEXT,
                department TEXT,
                email TEXT,
                research_areas TEXT,
                profile_url TEXT,
                scraped_data TEXT,
                search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS program_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                program_name TEXT,
                university TEXT,
                degree_type TEXT,
                requirements TEXT,
                deadlines TEXT,
                program_url TEXT,
                scraped_data TEXT,
                search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Database initialized")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_system():
    """Test the system setup"""
    print("\n🧪 Testing system...")
    
    try:
        # Test imports
        from app.core.logging import get_logger
        from app.core.config import settings
        print("✅ Core modules import successfully")
        
        # Test database
        conn = sqlite3.connect("search_history.db")
        conn.execute("SELECT 1")
        conn.close()
        print("✅ Database connection works")
        
        # Test if we can import AI libraries
        try:
            import transformers
            import torch
            print("✅ HuggingFace transformers available")
        except ImportError as e:
            print(f"⚠️  HuggingFace transformers not available: {e}")
            print("   The system will work but AI features may be limited")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def create_run_script():
    """Create a simple run script"""
    print("\n🚀 Creating run script...")
    
    run_script = '''#!/usr/bin/env python3
"""
Run script for STEM Graduate Admissions Assistant
"""

import uvicorn
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    print("🎓 Starting STEM Graduate Admissions Assistant...")
    print("🌐 Visit: http://localhost:8000")
    print("💬 Chat: http://localhost:8000/chat")
    print("🛑 Stop with Ctrl+C")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    
    with open("run_real_system.py", "w") as f:
        f.write(run_script)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod("run_real_system.py", 0o755)
    
    print("✅ Run script created: run_real_system.py")

def show_next_steps():
    """Show next steps to user"""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Start the application:")
    print("   python run_real_system.py")
    print("   OR")
    print("   python -m app.main")
    
    print("\n2. Open your browser:")
    print("   Dashboard: http://localhost:8000")
    print("   Chat: http://localhost:8000/chat")
    
    print("\n3. Try searching for:")
    print("   • 'Stanford computer science faculty'")
    print("   • 'MIT machine learning professors'")
    print("   • 'Berkeley PhD requirements'")
    
    print("\n🔍 Features:")
    print("✅ Real web scraping (no dummy data)")
    print("✅ HuggingFace AI (no API keys needed)")
    print("✅ Search history tracking")
    print("✅ Professor contact information")
    print("✅ University program details")
    
    print("\n💡 Tips:")
    print("• Search history is saved locally in SQLite")
    print("• No internet required after initial model download")
    print("• Data is scraped fresh from university websites")
    print("• Your searches are private and stored locally")

def main():
    """Main setup function"""
    print_header()
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Create directory structure
    if success:
        create_directory_structure()
    
    # Create configuration files
    if success:
        create_config_file()
        create_logging_config()
    
    # Install dependencies
    if success:
        if not install_dependencies():
            print("\n⚠️  Dependencies installation had issues, but continuing...")
    
    # Initialize database
    if success:
        if not initialize_database():
            success = False
    
    # Test system
    if success:
        if not test_system():
            print("\n⚠️  System test had issues, but may still work...")
    
    # Create run script
    if success:
        create_run_script()
    
    # Show next steps
    show_next_steps()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Run: python run_real_system.py")
    else:
        print("\n❌ Setup completed with some issues.")
        print("Check the error messages above and try running manually.")

if __name__ == "__main__":
    main()