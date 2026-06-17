# 路径规划智能体 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 先装共享库
COPY common/python /app/common/python
RUN pip install --no-cache-dir -e /app/common/python

# 再装本服务依赖
COPY agents/path-planner/requirements.txt /app/agents/path-planner/requirements.txt
RUN pip install --no-cache-dir -r /app/agents/path-planner/requirements.txt

# 拷贝源码
COPY agents/path-planner /app/agents/path-planner

WORKDIR /app/agents/path-planner
ENV PYTHONUNBUFFERED=1
EXPOSE 8091

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8091"]
