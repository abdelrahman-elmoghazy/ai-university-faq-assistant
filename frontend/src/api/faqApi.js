import axiosClient from './axiosClient'

export const faqApi = {
  askQuestion: (data) => axiosClient.post('/faq/ask', data),
  getHistory: () => axiosClient.get('/faq/history'),
  getQuestions: () => axiosClient.get('/faq/questions'),
  getQuestion: (id) => axiosClient.get(`/faq/questions/${id}`),
  getConversations: () => axiosClient.get('/faq/conversations'),
}
