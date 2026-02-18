# PRIME Mobile API — Cloud Run Container
FROM node:20-slim

WORKDIR /app

# Copy package files and install dependencies
COPY backend/package*.json ./backend/
RUN cd backend && npm ci --only=production

# Copy backend source
COPY backend/ ./backend/

# Copy PWA frontend (served by Express)
COPY mobile-pwa/ ./mobile-pwa/

# Set working directory to backend
WORKDIR /app/backend

# Cloud Run sets PORT env var
ENV NODE_ENV=production
EXPOSE 8080

CMD ["node", "server.js"]
