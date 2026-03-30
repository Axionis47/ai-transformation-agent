# ---- Stage 1: Build Next.js frontend ----
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# ---- Stage 2: Production image ----
FROM python:3.11-slim

# Install Node.js runtime for Next.js standalone server
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY api/ api/
COPY core/ core/
COPY services/ services/
COPY engines/ engines/
COPY config/ config/
COPY prompts/ prompts/
COPY data/ data/

# Next.js standalone output
COPY --from=frontend-build /frontend/.next/standalone /app/frontend
COPY --from=frontend-build /frontend/.next/static /app/frontend/.next/static

# Startup script — runs API + frontend
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]
