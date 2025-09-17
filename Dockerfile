FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装curl（用于API请求）
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 暴露端口（Render会自动设置PORT环境变量）
EXPOSE $PORT

# 启动命令
CMD ["python", "simple_server.py"]