import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development, proxy /api to the FastAPI backend so the frontend can use
// same-origin relative URLs. In production the API base is set via VITE_API_BASE.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
