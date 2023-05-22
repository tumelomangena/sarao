from fastapi import FastAPI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import ElasticVectorSearch

from config import openai_api_key

embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)

db = ElasticVectorSearch(
    elasticsearch_url="http://localhost:9200",
    index_name="elastic-index",
    embedding=embedding,
)
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    chain_type="stuff",
    retriever=db.as_retriever(),
)

@app.get("/books")
async def index():
    return {"books": db}

@app.get("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}


@app.post("/divide")
async def divide(dividend: int, divisor: int):
    return {"quotient":dividend/divisor}

