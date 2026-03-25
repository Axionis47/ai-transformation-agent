FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY api/ api/
COPY core/ core/
COPY services/ services/
COPY engines/ engines/
COPY config/ config/
COPY prompts/ prompts/
COPY data/ data/

EXPOSE 8080

CMD ["gunicorn", "api.app:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "300"]
