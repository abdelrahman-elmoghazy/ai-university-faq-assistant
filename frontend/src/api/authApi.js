import axiosClient from './axiosClient'

export const authApi = {
  register: (data) => axiosClient.post('/auth/register', data),
  login: (data) => axiosClient.post('/auth/login', data),
  loginWithGoogle: (accessToken) => axiosClient.post('/auth/oauth/google', { access_token: accessToken }),
  loginWithGithub: (code) => axiosClient.post('/auth/oauth/github', { code }),
  logout: () => axiosClient.post('/auth/logout'),
  getMe: () => axiosClient.get('/auth/me'),
  refresh: (refreshToken) => axiosClient.post('/auth/refresh', { refresh_token: refreshToken }),
}
