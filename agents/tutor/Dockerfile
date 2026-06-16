# ── 辅导智能体 Dockerfile ───────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 使用精简镜像，无需额外系统依赖

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY src/ ./src/

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import http.client; conn=http.client.HTTPConnection('localhost:8010'); conn.request('GET','/health'); resp=conn.getresponse(); exit(0 if resp.status==200 else 1)"

EXPOSE 8010

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8010"]
