import axiosClient from './axiosClient'

export const fileApi = {
  upload: (formData) =>
    axiosClient.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }),
  getMyFiles: () => axiosClient.get('/files/my-files'),
  getFile: (id) => axiosClient.get(`/files/${id}`),
  verifyIntegrity: (id) => axiosClient.get(`/files/${id}/verify`),
}
