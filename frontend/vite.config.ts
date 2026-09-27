import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Configuración de Vite: https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Puerto fijo: el CORS del backend admite :5173 (y :8080 de Docker). Si está ocupado, falla en vez de
  // arrancar en otro puerto donde todas las peticiones terminan en "Sin conexión".
  server: { port: 5173, strictPort: true },
  preview: { port: 5173, strictPort: true },
})
