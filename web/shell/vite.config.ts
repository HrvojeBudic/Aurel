import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev-only: the Front server (F5) is a stdlib HTTP server on its own port and
// sends no CORS headers, so the browser must reach it same-origin. The proxy
// forwards the one door (`/proposals`), the read projections (`/read/*`), the
// health probe and the `/ws` stream to `AUREL_FRONT_BASE` (default :8787).
// Run with VITE_AUREL_FRONT_BASE= (empty) so `frontClient` uses same-origin paths.
const FRONT_TARGET = process.env.AUREL_FRONT_BASE ?? "http://127.0.0.1:8787";

export default defineConfig({
  plugins: [react()],
  root: ".",
  publicDir: "public",
  server: {
    proxy: {
      "/health": { target: FRONT_TARGET, changeOrigin: true },
      "/read": { target: FRONT_TARGET, changeOrigin: true },
      "/proposals": { target: FRONT_TARGET, changeOrigin: true },
      "/ws": { target: FRONT_TARGET, changeOrigin: true, ws: true },
    },
  },
});
