import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:5001',
                changeOrigin: true,
                secure: false,
            },
            '/auth': {
                target: 'http://127.0.0.1:5001',
                changeOrigin: true,
                secure: false,
            },
            // Only proxy specific admin API endpoints, so React Router can handle the base /admin route
            '^/admin/(stats|users|sessions)': {
                target: 'http://127.0.0.1:5001',
                changeOrigin: true,
                secure: false,
            }
        }
    }
});
