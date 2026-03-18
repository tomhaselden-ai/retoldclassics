import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/accounts": "http://127.0.0.1:8000",
      "/readers": "http://127.0.0.1:8000",
      "/stories": "http://127.0.0.1:8000",
      "/classics": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
      "/dashboard": "http://127.0.0.1:8000",
      "/worlds": "http://127.0.0.1:8000",
      "/continuity": "http://127.0.0.1:8000",
      "/safety": "http://127.0.0.1:8000",
      "/alexa": "http://127.0.0.1:8000"
    }
  }
});
