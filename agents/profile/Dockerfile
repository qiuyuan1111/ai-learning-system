FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制共享包
COPY common/ /app/common/
RUN pip install -e /app/common/

# 安装项目依赖
COPY agents/profile/requirements.txt /app/agents/profile/
RUN pip install --no-cache-dir -r /app/agents/profile/requirements.txt

# 复制源码
COPY agents/profile/src/ /app/agents/profile/src/

EXPOSE 8081

CMD ["uvicorn", "agents.profile.src.main:app", "--host", "0.0.0.0", "--port", "8081"]
