import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:9000',
});

api.interceptors.request.use((config) => {
    const token = document.cookie.match(/(^|;\s*)token=([^;]*)/)?.[2];
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;