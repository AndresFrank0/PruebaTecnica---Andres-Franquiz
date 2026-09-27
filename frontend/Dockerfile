# Etapa 1: compila la SPA. Node 24: la versión con la que se desarrolló.
FROM node:24-alpine AS build
WORKDIR /app
# Primero las dependencias: la capa de npm ci se reutiliza mientras package.json y el lockfile no cambien.
COPY package*.json ./
RUN npm ci
COPY . .
# Vite incrusta la URL de la API en el bundle al compilar: se fija aquí, no al arrancar el contenedor.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Etapa 2: nginx sirve los archivos estáticos; la imagen final no lleva Node ni node_modules.
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
