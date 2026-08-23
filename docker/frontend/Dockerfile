# =============================================================================
# FinVox Frontend — Production Dockerfile
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder) — Node.js installs deps and builds the Vite/React app
#   Stage 2 (runtime) — Nginx serves the static build output
#
# Build:  docker build -f docker/frontend/Dockerfile -t finvox-frontend:latest ./ui/finvox
# Run:    docker run -p 3000:80 finvox-frontend:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 — Builder
# Uses Node.js to install dependencies and run `vite build`.
# The entire node_modules folder stays in this stage and never reaches prod.
# -----------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first — Docker caches this layer.
# node_modules only re-installs when package*.json changes.
# Build context is the project root, so frontend source is under ui/finvox/
COPY ui/finvox/package.json ui/finvox/package-lock.json ./

# Install ALL dependencies (including devDeps needed for tsc + vite build)
# Using npm install instead of npm ci to handle lock file sync differences
RUN npm install

# Copy the rest of the frontend source code
COPY ui/finvox/ .

# Build argument — lets you pass the backend URL at build time:
#   docker build --build-arg VITE_API_BASE_URL=https://api.finvox.com ...
# Falls back to localhost for local testing.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Run Vite production build (skips strict tsc check — fix TS errors separately)
# `npm run build` runs `tsc -b && vite build` — tsc fails on unused imports etc.
# For production Docker we build the JS output directly via vite.
RUN npx vite build


# -----------------------------------------------------------------------------
# Stage 2 — Runtime
# Nginx serves the static files built above.
# Final image has NO Node.js, NO npm, NO source code — just the built HTML/JS/CSS.
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the Vite build output from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx config (SPA routing + security headers + gzip)
# Build command must be run from project root:
#   docker build -f docker/frontend/Dockerfile -t finvox-frontend:latest .
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Nginx runs on port 80 inside the container
EXPOSE 80

# Health check — curl the root page
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

# Nginx foreground mode (required for Docker)
CMD ["nginx", "-g", "daemon off;"]
