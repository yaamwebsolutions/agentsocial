# =============================================================================
# Agent Twitter - Frontend Dockerfile
# Multi-stage build for optimal image size
# =============================================================================

FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the application
RUN npm run build

# =============================================================================
# Final stage - Production with nginx
# =============================================================================
FROM nginx:alpine

# Set labels
LABEL maintainer="Agent Twitter Contributors"
LABEL description="Agent Twitter Frontend - React + Vite"
LABEL version="1.0.0"

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
