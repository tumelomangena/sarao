import uvicorn
from fastapi import FastAPI
from typing import List
from pydantic import BaseModel, Field

app = FastAPI()

class Student(BaseModel):
	dividend: int
	divisor :int

@app.post("/divide/")
async def divide():
	return {"quotient":dividend/divisor}
