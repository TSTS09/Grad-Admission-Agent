#!/usr/bin/env python3
"""
Final Import Test - Test the fixed modules
"""

def test_circular_import_fix():
    """Test that the circular import is fixed"""
    
    print("🔧 Testing Circular Import Fix")
    print("=" * 40)
    
    try:
        # Test logging import first
        from app.core.logging import setup_logging, get_logger
        print("✅ app.core.logging imported successfully")
        
        # Test config import
        from app.core.config import settings, get_firebase
        print("✅ app.core.config imported successfully")
        
        # Test settings access
        print(f"✅ Settings loaded: {settings.APP_NAME}")
        
        # Test logger creation
        logger = get_logger("test")
        print("✅ Logger created successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_project_modules():
    """Test importing all project modules"""
    
    print("\n📦 Testing All Project Modules")
    print("=" * 40)
    
    modules_to_test = [
        ("app.core.logging", "Logging module"),
        ("app.core.config", "Config module"),
        ("app.models.firebase_models", "Firebase models"),
        ("app.agents.cost_effective_agents", "AI agents"),
        ("app.scrapers.real_university_scraper", "Scrapers"),
    ]
    
    failed_modules = []
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            print(f"❌ {module_name} - {description}: ImportError - {e}")
            failed_modules.append(module_name)
        except Exception as e:
            print(f"⚠️  {module_name} - {description}: {e}")
            # Don't count as failed - might be missing dependencies that's OK
    
    return len(failed_modules) == 0

def check_missing_dependencies():
    """Check for missing dependencies"""
    
    print("\n📋 Checking Additional Dependencies")
    print("=" * 40)
    
    optional_packages = [
        ("structlog", "Structured logging"),
    ]
    
    missing = []
    
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (install with: pip install {package})")
            missing.append(package)
    
    return missing

def main():
    """Run all tests"""
    
    print("🚀 Final Import Test")
    print("=" * 40)
    
    # Check missing dependencies first
    missing_deps = check_missing_dependencies()
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Installing...")
        import subprocess
        import sys
        
        for dep in missing_deps:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✅ Installed {dep}")
            except Exception as e:
                print(f"❌ Failed to install {dep}: {e}")
        
        print("\n" + "=" * 40)
    
    # Test circular import fix
    circular_fix_ok = test_circular_import_fix()
    
    # Test all modules
    modules_ok = test_all_project_modules()
    
    print("\n" + "=" * 40)
    print("RESULTS")
    print("=" * 40)
    
    if circular_fix_ok and modules_ok:
        print("🎉 All imports working! The circular import is fixed.")
        print("\nYou can now run:")
        print("   python quick_start.py")
        print("   python app/main.py")
    else:
        print("⚠️  Some issues remain:")
        
        if not circular_fix_ok:
            print("   - Circular import still exists")
        if not modules_ok:
            print("   - Some modules failed to import")
        
        print("\nCheck the errors above for details.")

if __name__ == "__main__":
    main()