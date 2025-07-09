#!/usr/bin/env python
import uvicorn
from ltc_crew.api import app

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
