A simple API script built using FastAPI.

To run the code follow the following steps:

Install FastAPI:

```pip3 install fastapi```

Install unicorn:

``` pip3 install uvicorn```

Run the following command to start the unicorn server tagging the API script:

```uvicorn main:app --reload```

Go to the URL: http://127.0.0.1:8000/divide?dividend=20&divisor=2 in order to access the results.

Lessons learned:

- FastAPI is a Python web framework used to building APIs and one of the fastest web frameworks of Python.
- When running the script in localhost, you can always access the automatically generated interactive documentation through this link: 
http://127.0.0.1:8000/docs
- Unicorn is used as a server to run the FastAPI since the FastAPI does not have a build-in development server. 
- You can also use curl on the terminal to access the results:
e.g curl -X 'GET'   'http://127.0.0.1:8000/divide?dividend=20&divisor=5'   -H 'accept: application/json'  

FastAPI follow REST architecture which is is a software architectural style. REST stand for RElational State Transfer and recommends the following architectural constraints:
- Uniform interface
- Statelessness
- Client-server
- Cacheability
- Layered system
- Code on demand

