# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY frontend/package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ ./

# Build application
RUN npm run build

# Production Stage (NGINX)
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
