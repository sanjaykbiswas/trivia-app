import uvicorn
import sys
import os
from pathlib import Path

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    print("Starting Trivia API server...")
    print("API documentation will be available at http://localhost:8000/docs")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)