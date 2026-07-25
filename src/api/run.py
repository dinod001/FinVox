import uvicorn
import os
import sys

# Ensure the root project directory is in the Python path
# so that imports like `src.infrastructure...` work correctly.
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_SRC)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

if __name__ == "__main__":
    """
    Entry point to run the FinVox FastAPI server from the api directory.
    """
    uvicorn.run(
        "src.api.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )
