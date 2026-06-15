FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY common/ /app/common/
RUN pip install -e /app/common/

COPY agents/tutor/requirements.txt /app/agents/tutor/
RUN pip install --no-cache-dir -r /app/agents/tutor/requirements.txt

COPY agents/tutor/src/ /app/agents/tutor/src/

EXPOSE 8082

CMD ["uvicorn", "agents.tutor.src.main:app", "--host", "0.0.0.0", "--port", "8082"]
