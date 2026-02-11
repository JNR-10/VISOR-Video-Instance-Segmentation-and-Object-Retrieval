import axios from 'axios'
import { Video, SegmentedObject, RetrieveResponse, AnalyticsEvent } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  uploadVideo: async (file: File): Promise<Video> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post('/api/videos', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getVideo: async (videoId: string): Promise<Video> => {
    const response = await apiClient.get(`/api/videos/${videoId}`)
    return response.data
  },

  logEvent: async (event: AnalyticsEvent): Promise<void> => {
    await apiClient.post('/api/events', event)
  },

  startProcessing: async (videoId: string): Promise<{ message: string; video_id: string }> => {
    const response = await apiClient.post('/api/process', {
      video_id: videoId,
    })
    return response.data
  },

  getProcessingStatus: async (videoId: string): Promise<{
    video_id: string
    status: string
    progress: number
    message: string
    logs: string[]
  }> => {
    const response = await apiClient.get(`/api/process/status/${videoId}`)
    return response.data
  },

  getTrackingData: async (videoId: string): Promise<any> => {
    const response = await apiClient.get(`/api/tracking/${videoId}`)
    return response.data
  },
}

export default api
