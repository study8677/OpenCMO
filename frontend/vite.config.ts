import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/",
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          /* Heavy 3D / graph lib — only loaded by GraphPage */
          "vendor-graph": ["three", "react-force-graph-3d", "react-force-graph-2d"],
          /* Chart lib — loaded by SEO / GEO / SERP / Community pages */
          "vendor-charts": ["recharts"],
          /* Markdown renderer — loaded by Reports + Chat */
          "vendor-markdown": ["react-markdown"],
        },
      },
    },
  },
});
