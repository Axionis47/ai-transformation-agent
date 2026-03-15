FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY agents/ agents/
COPY orchestrator/ orchestrator/
COPY ops/ ops/
COPY rag/ rag/
COPY infra/ infra/
COPY prompts/ prompts/
COPY tests/fixtures/ tests/fixtures/

# Cloud Run uses PORT env var, default 8080
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
