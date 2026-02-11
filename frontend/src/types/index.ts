export interface Video {
  video_id: string
  url: string
  title?: string
  description?: string
  duration?: number
  width?: number
  height?: number
  fps?: number
  created_at: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface SegmentedObject {
  object_id: string
  mask_url: string
  crop_url: string
  bbox: BoundingBox
  confidence: number
  timestamp_ms: number
  category?: string
}

export interface Product {
  product_id: string
  title: string
  brand?: string
  price?: number
  currency?: string
  image_url: string
  buy_url: string
  category?: string
  confidence: number
}

export interface RetrieveResponse {
  object_id: string
  products: Product[]
  processing_time_ms: number
}

export interface AnalyticsEvent {
  event_type: string
  video_id?: string
  object_id?: string
  product_id?: string
  timestamp_ms?: number
  metadata?: Record<string, any>
}
