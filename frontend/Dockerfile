# Frontend Dockerfile — development
FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
