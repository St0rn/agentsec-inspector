import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { strictPort: true },
  envPrefix: ["VITE_", "TAURI_"],
  build: { target: "es2021", minify: "esbuild", sourcemap: false },
  test: { environment: "jsdom", setupFiles: "./src/test/setup.ts", coverage: { provider: "v8", reporter: ["text", "json"] } }
});
