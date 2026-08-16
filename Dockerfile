# Frontend build stage
FROM node:20 AS frontend-build
ARG VITE_API_BASE=""
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# Backend runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ /app/backend
COPY torrent_processor.py /app/torrent_processor.py
# 配置不在镜像中携带凭据：目录由后端按需创建，运行时通过卷挂载或环境变量提供
# /app/config 是卷挂载点，目录创建与属主设置必须在切换 USER 之前完成
RUN mkdir -p /app/config
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
RUN chmod +x /app/entrypoint.sh
# 以非特权用户运行容器，避免 root 运行带来的风险
RUN useradd -r -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
# 健康检查走静态页端点（不受 TR_API_TOKEN 影响）
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)" || exit 1
CMD ["/app/entrypoint.sh"]
