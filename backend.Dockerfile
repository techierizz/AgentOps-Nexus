FROM python:3.12-slim

WORKDIR /app

# Install git since the agent needs git subprocess capabilities
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["python", "backend/main.py"]
