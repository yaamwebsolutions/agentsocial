import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
const apiBaseUrl = process.env.VITE_API_BASE_URL || process.env.VITE_API_URL || "http://localhost:8000"

export default defineConfig({
  base: '/',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: apiBaseUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(apiBaseUrl)
  }
});
