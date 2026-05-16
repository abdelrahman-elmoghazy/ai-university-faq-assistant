import axiosClient from './axiosClient'

export const adminApi = {
  getStats: () => axiosClient.get('/admin/stats'),
  getAllFiles: () => axiosClient.get('/admin/files'),
  getAuditLogs: (limit = 50) => axiosClient.get(`/admin/audit-logs?limit=${limit}`),
  getRecentQueries: (limit = 20) => axiosClient.get(`/admin/recent-queries?limit=${limit}`),
  // From auth-service admin endpoints
  getUsers: (page = 1) => axiosClient.get(`/admin/users?page=${page}`),
}
