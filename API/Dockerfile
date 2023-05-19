# syntax=docker/dockerfile:1

FROM ubuntu:18.04

WORKDIR /API

RUN apt-get update
RUN apt-get install -y python3
RUN apt install -y python3-pip
RUN python3 -m pip install fastapi 
RUN python3 -m pip install uvicorn
COPY . .
#CMD ["python3", "main.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
EXPOSE 4321
