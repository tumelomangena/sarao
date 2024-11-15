from fastapi import FastAPI
from elasticsearch import Elasticsearch

app = FastAPI()

es = Elasticsearch(
    hosts=["https://localhost:9200"], 
    basic_auth=['elastic', 'OnEiLeMangEna'], 
    verify_certs=False)


@app.get("/books")
async def index():
    return {"books": es.search()}
