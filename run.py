import os
import subprocess
import sys

def check_dependencies():
    """Check if required dependencies are installed."""
    print("[SETUP] Checking dependencies...")
    try:
        import fastapi
        print("[SETUP] ✓ FastAPI installed")
        import supabase
        print("[SETUP] ✓ Supabase installed")
        import pandas
        print("[SETUP] ✓ Pandas installed")
        import requests
        print("[SETUP] ✓ Requests installed")
        import uvicorn
        print("[SETUP] ✓ Uvicorn installed")
        print("[SETUP] All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"[SETUP] ✗ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("[SETUP] Installing required dependencies...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "websockets",
        "jinja2",
        "supabase",
        "pandas",
        "requests"
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + required_packages)
    print("[SETUP] Dependencies installed successfully.")

def check_ollama():
    """Check if Ollama is running."""
    print("[SETUP] Checking if Ollama is running...")
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            llama_models = [m for m in models if "llama" in m["name"].lower()]
            if llama_models:
                print(f"[SETUP] ✓ Ollama is running with Llama models: {', '.join([m['name'] for m in llama_models])}")
                return True
            else:
                print("[SETUP] ✗ Ollama is running but no Llama models found. Please install llama3:1b model.")
                return False
        else:
            print(f"[SETUP] ✗ Ollama API returned unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"[SETUP] ✗ Error checking Ollama: {e}")
        print("[SETUP] Please ensure Ollama is installed and running with the llama3:1b model.")
        return False

def setup_sample_data():
    """Create sample data if it doesn't exist."""
    print("[SETUP] Checking for sample data...")
    if not os.path.exists("sample_tickets.csv"):
        print("[SETUP] Sample data file not found.")
        print("[SETUP] Setting up sample data...")
        try:
            from database.supabase_client import SupabaseClient
            client = SupabaseClient()
            print("[SETUP] Sample data setup complete.")
        except Exception as e:
            print(f"[SETUP] Error setting up sample data: {e}")
    else:
        print("[SETUP] ✓ Sample data file found.")

def start_app():
    """Start the FastAPI app."""
    print("[SETUP] Starting the AI-Driven Customer Support System...")
    subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    print("[SETUP] FastAPI server has been launched.")

if __name__ == "__main__":
    print("=" * 80)
    print("AI-Driven Customer Support System Setup")
    print("=" * 80)
    
    if not check_dependencies():
        print("[SETUP] Installing missing dependencies...")
        install_dependencies()
    
    if not check_ollama():
        print("[SETUP] Warning: Proceeding without verifying Ollama. The application may not function correctly.")
    
    setup_sample_data()
    start_app()
    
    print("\n[SETUP] Setup complete! Your AI-Driven Customer Support System should now be running.")
    print("[SETUP] You can access it at http://localhost:8000")
    print("\n[SETUP] If you encounter any issues, please check the following:")
    print("[SETUP] 1. Ensure Ollama is running with the llama3:1b model installed")
    print("[SETUP] 2. Verify all dependencies are correctly installed")
    print("[SETUP] 3. Check that Supabase credentials are set correctly (if applicable)")
