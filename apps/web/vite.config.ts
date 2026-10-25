import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../..', 'VITE_');
  return { plugins: [react(), tailwindcss()], envDir: '../..',
    define: { 'import.meta.env.VITE_MOCK': JSON.stringify(env.VITE_MOCK ?? '1') } };
});