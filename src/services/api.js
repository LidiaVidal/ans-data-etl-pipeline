import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // Endereço do seu futuro backend Python
  timeout: 10000,
});

export default api;