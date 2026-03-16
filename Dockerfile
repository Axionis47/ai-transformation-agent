FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ agents/
COPY orchestrator/ orchestrator/
COPY ops/ ops/
COPY rag/ rag/
COPY infra/ infra/
COPY evals/ evals/
COPY tools/ tools/
COPY prompts/ prompts/
COPY tests/fixtures/ tests/fixtures/
COPY app.py .

ENV PORT=8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
