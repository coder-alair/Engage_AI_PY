# RecruiAI API Project

AI APIs For RecruitAI using FastAPI and DeepInfra

## Prerequisites

- Python 3.10+
- Poetry

## Quick Start

1. Clone the repository:

## Quick Start

1. Clone the repository:
   `git clone https://gitlab.oodleslab.com/oodles/engage-ai-py.git`

## Configuration

Environment variables are stored in the `.env` file. Copy `.env.example` to `.env` and adjust as needed
2. Navigate to the project directory:
   `cd engage-ai-py`

3. Install dependencies with Poetry:

   ```
   cd services/
   poetry install
   ```

4. Run the FastAPI application:
   `poetry run uvicorn chatbot_api.main:app --reload`

5. Access the API at `http://localhost:8000`

6. View API documentation at `http://localhost:8000/docs`

## Project Structure

```
   .
   ├── ci_cd
   ├── infrastructure
   ├── lib
   ├── Readme.md
   ├── services
   │   ├── engage_api
   │   │   ├── llm.py
   │   │   ├── main.py
   │   │   ├── schemas.py
   │   │   └── settings.py
   │   ├── neondb
   │   │   ├── models.py
   │   ├── poetry.lock
   │   ├── pyproject.toml
   │   └── tests
   │       ├── e2e
   │       ├── integrations
   │       │   └── test_backend_api
   │       │       └── test_main.py
   │       └── unit
   └── tools

```

## Configuration

Environment variables are stored in the `.env` file. Copy `.env.example` to `.env` and adjust as needed.

## Testing

Run tests with:
`pytest`
