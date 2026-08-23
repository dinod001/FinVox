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
    Entry point to run the FinVox FastAPI server.
    Set DEV_MODE=1 in your environment to enable hot-reload during development.
    In production/desktop mode, reload is disabled to avoid the ~60-80s WatchFiles
    reloader overhead on startup.
    """
    dev_mode = os.getenv("DEV_MODE", "0") == "1"
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "src.api.main:app", 
        host=host, 
        port=port, 
        reload=dev_mode,        # False by default — removes reloader process overhead
        log_level="info"
    )
