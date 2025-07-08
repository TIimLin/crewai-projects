#!/usr/bin/env python
import uvicorn
from my_first_crew.api import app

def run_server():
    """
    Run the Uvicorn server.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()
