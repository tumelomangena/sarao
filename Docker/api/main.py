from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/books")
async def api_data():
    return os.system("open \"\" https://localhost:9200/books/_search")


@app.get("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}


@app.post("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}

