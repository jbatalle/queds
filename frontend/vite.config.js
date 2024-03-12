import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite';
import {fileURLToPath, URL} from "url";
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        Components()
    ], resolve: {
        alias: {
            '@/': `${path.resolve(__dirname, 'src')}/`
        }
    }
})
