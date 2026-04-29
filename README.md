# Temple API Gateway

Public FastAPI gateway for the temple mobile app.

## Responsibilities

- expose a stable `/api/v1` surface to the mobile app
- centralize request IDs, logging, and auth middleware later
- route calls to downstream services

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

## Render start command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

