import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types'),
      '@gateway': path.resolve(__dirname, './src/gateway'),
    },
  },
  build: {
    target: 'node18',
    outDir: 'dist',
    lib: {
      entry: 'src/main.tsx',
      name: 'CielTUI',
      fileName: 'ciel-tui',
      formats: ['es'],
    },
    rollupOptions: {
      external: ['ink', 'react', 'react-reconciler'],
      output: {
        globals: {
          ink: 'Ink',
          react: 'React',
          'react-reconciler': 'ReactReconciler',
        },
      },
    },
  },
  define: {
    'process.env.NODE_ENV': '"production"',
  },
});