# 资源生成编排器 Dockerfile
FROM python:3.11-slim

# 中文字体（PPT/PDF 渲染需要）+ 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装共享库（利用层缓存）
COPY common/python /app/common/python
RUN pip install --no-cache-dir -e /app/common/python

# 再装本服务依赖
COPY agents/resource-gen/requirements.txt /app/agents/resource-gen/requirements.txt
RUN pip install --no-cache-dir -r /app/agents/resource-gen/requirements.txt

# 拷贝源码
COPY agents/resource-gen /app/agents/resource-gen

WORKDIR /app/agents/resource-gen
ENV PYTHONUNBUFFERED=1
EXPOSE 8090

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8090"]
