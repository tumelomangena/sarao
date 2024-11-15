## Docker compose project


The docker compose project covers the implimentation of multi-container where we create three docker containers to run **kibana, elasticsearch and api project** . 


Follow the steps below in order to run the project.

STEP 1:

```Edit the .env file to suite your needs:```


STEP 2: Run the following command on the terminal in-order to build containers.

```docker-compose up -d```

STEP 3: Go to the following API address to access elasticseach content:

```https://localhost:4321/books```


username: elastic

password: <ELASTIC_PASSWORD= > stored in .env file.


