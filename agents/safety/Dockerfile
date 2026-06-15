FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY common/ /app/common/
RUN pip install -e /app/common/

COPY agents/safety/requirements.txt /app/agents/safety/
RUN pip install --no-cache-dir -r /app/agents/safety/requirements.txt

COPY agents/safety/src/ /app/agents/safety/src/

EXPOSE 8083

CMD ["uvicorn", "agents.safety.src.main:app", "--host", "0.0.0.0", "--port", "8083"]
