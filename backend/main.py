from dotenv import load_dotenv
load_dotenv()

import sys
import os

# Ensure the current directory is in the path so we can import from 'app' and 'agents'
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.append(backend_root)

from app.main import app

if __name__ == "__main__":
    import uvicorn
    # Use the string "main:app" for reload to work correctly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
