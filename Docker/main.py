from fastapi import FastAPI

app = FastAPI()

@app.get("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}


@app.post("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}
