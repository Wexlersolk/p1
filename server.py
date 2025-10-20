import uvicorn
from src.api.app import create_app
from src.api.config import API_CONFIG

app = create_app()

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["reload"],
        workers=API_CONFIG["workers"]
    )