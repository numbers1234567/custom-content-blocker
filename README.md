# Custom Content Blocker

A website which gives users options to control their social media feed.

## Environment Setup

Before doing anything, if you're on Windows, you may want to disable automatic conversion of line endings in your git config:

    git config --global core.autocrlf false

Clone the repo:

    git clone https://github.com/numbers1234567/custom-content-blocker.git

Then (optionally) switch to the development branch with

    git checkout staging

### Backend

For the *curator*, *postgres-db-manager*, and *public-api*, I have a *local.env* which defines environment variables in each directory.

#### curator

    CONTENT_CURATION_POSTGRES_DB_NAME=postgres
    CONTENT_CURATION_POSTGRES_HOST=host.docker.internal
    CONTENT_CURATION_POSTGRES_PASSWORD=1234
    CONTENT_CURATION_POSTGRES_PORT=5432
    CONTENT_CURATION_POSTGRES_USER=postgres

#### postgres-db-manager

    CONTENT_CURATION_POSTGRES_DB_NAME=postgres
    CONTENT_CURATION_POSTGRES_HOST=host.docker.internal
    CONTENT_CURATION_POSTGRES_PASSWORD=1234
    CONTENT_CURATION_POSTGRES_PORT=5432
    CONTENT_CURATION_POSTGRES_USER=postgres

#### public-api

    CONTENT_CURATION_POST_DB_MANAGER = http://host.docker.internal:8000
    CONTENT_CURATION_CURATOR = http://host.docker.internal:8002
    CONTENT_CURATION_GOOGLE_CLIENT_ID = 194668652482-o3cimds7musrstnde6oi1avbc51p7sqk.apps.googleusercontent.com

Make sure Docker is installed on your system. I use Docker Desktop as I am new to it.

To run the backend,

    cd backend
    docker compose up --build

You may need to run this twice before it works.

(Optional) install psql to directly interact with your local DB with

    psql -U postgres

and enter 1234 as the password

### Frontend

Install Node if you haven't already.

Environment variables are stored in a .env.local file:

    NEXT_PUBLIC_CURATE_API_URL=http://localhost:8001
    NEXT_PUBLIC_GOOGLE_CLIENT_APP_ID=194668652482-o3cimds7musrstnde6oi1avbc51p7sqk

Now you can run the frontend with

    cd user-view
    pnpm install
    npm run dev

*pnpm install* is only necessary on the first run or if a new package is added.


### Testing

For local testing, I recommend you use your preferred Python package manager such as Anaconda.

#### Backend Unit Tests

If you want to test a Python script *A*, there should be an associated *requirements.txt file*. Install with

    pip install -r requirements.txt

and run the file with

    python A.py

#### Load Tests

This is stored in the *tests* directory.

Run the load test UI with

    cd tests
    locust

