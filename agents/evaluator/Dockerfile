FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY common/ /app/common/
RUN pip install -e /app/common/

COPY agents/evaluator/requirements.txt /app/agents/evaluator/
RUN pip install --no-cache-dir -r /app/agents/evaluator/requirements.txt

COPY agents/evaluator/src/ /app/agents/evaluator/src/

EXPOSE 8080

CMD ["uvicorn", "agents.evaluator.src.main:app", "--host", "0.0.0.0", "--port", "8080"]
