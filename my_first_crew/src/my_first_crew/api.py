from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from my_first_crew.crew import MyFirstCrew

app = FastAPI()

class CrewInputs(BaseModel):
    destination: str
    duration: str
    interests: str
    start_date: str
    end_date: str

@app.post("/invoke")
async def invoke_crew(inputs: CrewInputs) -> Dict:
    """
    Invoke the crew with the given inputs and return the result.
    """
    inputs_dict = inputs.dict()
    try:
        result = MyFirstCrew().crew().kickoff(inputs=inputs_dict)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)} 