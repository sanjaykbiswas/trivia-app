# check_dependencies.py
import sys

def check_dependencies():
    try:
        import supabase
        print(f"Supabase version: {supabase.__version__}")
    except (ImportError, AttributeError):
        print("Supabase package installed but version not found")
        
    try:
        import httpx
        print(f"httpx version: {httpx.__version__}")
    except (ImportError, AttributeError):
        print("httpx not installed or version not found")

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    check_dependencies()