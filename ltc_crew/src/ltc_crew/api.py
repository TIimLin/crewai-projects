from fastapi import FastAPI
from pydantic import BaseModel
from ltc_crew.crew import LtcCrew
import os
from datetime import datetime

app = FastAPI()

class UserQuery(BaseModel):
    user_query: str

@app.post("/invoke")
async def invoke_crew(query: UserQuery):
    """
    Invokes the LtcCrew with a user query and saves the result to a markdown file.
    """
    inputs = {'user_query': query.user_query}
    crew_result = LtcCrew().crew().kickoff(inputs=inputs)

    # --- Add file saving logic ---
    # Create a reports directory if it doesn't exist
    if not os.path.exists('reports'):
        os.makedirs('reports')

    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"reports/report_{timestamp}.md"

    # Save the result to the markdown file
    # The output from kickoff() is a CrewOutput object, we need its .raw attribute for the string.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(crew_result.raw)
    # --- End of file saving logic ---

    # Convert the full CrewOutput object to a dictionary for a detailed response
    detailed_response = crew_result.model_dump()
    detailed_response['report_path'] = file_path

    return detailed_response

@app.get("/")
async def root():
    return {"message": "LTC Crew API is running."} 