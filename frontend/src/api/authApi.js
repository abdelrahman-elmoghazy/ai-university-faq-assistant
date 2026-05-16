import axiosClient from './axiosClient'

export const authApi = {
  register: (data) => axiosClient.post('/auth/register', data),
  login: (data) => axiosClient.post('/auth/login', data),
  logout: () => axiosClient.post('/auth/logout'),
  getMe: () => axiosClient.get('/auth/me'),
  refresh: (refreshToken) => axiosClient.post('/auth/refresh', { refresh_token: refreshToken }),
}
