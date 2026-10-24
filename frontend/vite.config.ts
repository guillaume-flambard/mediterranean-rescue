/// <reference types="vitest/config" />
import babel from "@rolldown/plugin-babel";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // React Compiler 1.0 memoizes components and hooks at build time (react.dev, installation).
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  test: { setupFiles: ["./src/test/setup.ts"] },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:8010",
      "/admin": "http://127.0.0.1:8010",
    },
  },
});
