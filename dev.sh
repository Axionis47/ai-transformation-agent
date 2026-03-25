#!/bin/bash
# One-command local dev startup: backend (8000) + frontend (3000)
# Usage: ./dev.sh

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
    echo -e "\n${CYAN}Shutting down...${NC}"
    kill $BE_PID $FE_PID 2>/dev/null
    wait $BE_PID $FE_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Clear stale ChromaDB so fresh engagements get ingested
if [ "$1" = "--fresh" ]; then
    echo -e "${CYAN}Clearing ChromaDB for fresh ingest...${NC}"
    rm -rf data/chroma_store
fi

# Backend
echo -e "${GREEN}Starting backend on :8000${NC}"
python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload &
BE_PID=$!

# Frontend
echo -e "${GREEN}Starting frontend on :3000${NC}"
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npx next dev --port 3000 &
FE_PID=$!
cd ..

echo -e "\n${GREEN}Ready:${NC}"
echo -e "  Backend:  http://localhost:8000/health"
echo -e "  Frontend: http://localhost:3000"
echo -e "  Press Ctrl+C to stop\n"

wait
