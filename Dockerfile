# Frontend build stage
FROM node:20 AS frontend-build
ARG VITE_API_BASE=""
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
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
COPY config/ /app/config/
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000
CMD ["/app/entrypoint.sh"]
