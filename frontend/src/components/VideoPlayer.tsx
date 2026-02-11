'use client'

import { useRef, useState, useEffect } from 'react'
import { Upload, Loader2 } from 'lucide-react'
import api from '@/lib/api'
import { Product } from '@/types'

interface VideoPlayerProps {
  onProductsFound: (products: Product[]) => void
}

interface TrackingData {
  video_id: string
  fps: number
  total_frames: number
  tracks_by_frame: Record<string, any[]>
  object_products: Record<string, any>
}

export default function VideoPlayer({ onProductsFound }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  
  const [videoId, setVideoId] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingMessage, setProcessingMessage] = useState('')
  const [processingLogs, setProcessingLogs] = useState<string[]>([])
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null)
  const [currentDetections, setCurrentDetections] = useState<any[]>([])
  const [videoAspectRatio, setVideoAspectRatio] = useState<'horizontal' | 'vertical'>('horizontal')
  const [renderKey, setRenderKey] = useState(0)

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const video = await api.uploadVideo(file)
      setVideoId(video.video_id)
      setVideoUrl(`${process.env.NEXT_PUBLIC_API_URL}${video.url}`)
      
      await api.logEvent({
        event_type: 'video_upload',
        video_id: video.video_id,
      })

      // Start automatic processing
      startVideoProcessing(video.video_id)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Failed to upload video')
    } finally {
      setIsUploading(false)
    }
  }

  const startVideoProcessing = async (videoId: string) => {
    setIsProcessing(true)
    setProcessingProgress(0)
    setProcessingMessage('Starting video processing...')
    setProcessingLogs([])

    try {
      // Trigger processing
      await api.startProcessing(videoId)

      // Clear any existing interval
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }

      // Poll for status
      pollIntervalRef.current = setInterval(async () => {
        try {
          const status = await api.getProcessingStatus(videoId)
          console.log('Processing status:', status)
          console.log('Progress:', status.progress, 'Message:', status.message)
          console.log('Logs count:', status.logs?.length || 0)
          
          // Update all state at once
          setProcessingProgress(status.progress)
          setProcessingMessage(status.message)
          setProcessingLogs(status.logs || [])
          setRenderKey(prev => prev + 1) // Force re-render
          
          if (status.logs && status.logs.length > 0) {
            console.log('Latest logs:', status.logs.slice(-3))
          }

          if (status.status === 'completed') {
            console.log('Processing completed! Loading tracking data...')
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current)
              pollIntervalRef.current = null
            }
            setIsProcessing(false)
            // Load tracking data
            await loadTrackingData(videoId)
          } else if (status.status === 'failed') {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current)
              pollIntervalRef.current = null
            }
            setIsProcessing(false)
            alert('Video processing failed')
          }
        } catch (error) {
          console.error('Status check failed:', error)
        }
      }, 2000) // Poll every 2 seconds
    } catch (error) {
      console.error('Failed to start processing:', error)
      setIsProcessing(false)
      alert('Failed to start video processing')
    }
  }

  const loadTrackingData = async (videoId: string) => {
    try {
      const data = await api.getTrackingData(videoId)
      setTrackingData(data)
      console.log('Loaded tracking data:', data)
    } catch (error) {
      console.error('Failed to load tracking data:', error)
    }
  }

  // Update canvas size on window resize
  useEffect(() => {
    const handleResize = () => {
      updateCanvasSize()
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [videoAspectRatio])

  // Render overlays on video
  useEffect(() => {
    if (!trackingData || !videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const maskCache: Record<string, HTMLImageElement> = {}

    const renderOverlays = async () => {
      const currentTime = video.currentTime * 1000 // Convert to ms
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Find closest frame
      const timestamps = Object.keys(trackingData.tracks_by_frame).map(Number)
      const closestTimestamp = timestamps.reduce((prev, curr) => 
        Math.abs(curr - currentTime) < Math.abs(prev - currentTime) ? curr : prev
      )

      const detections = trackingData.tracks_by_frame[closestTimestamp] || []
      
      // Update current detections for clickable overlays
      setCurrentDetections(detections)

      // Helper function to get color for category
      const getCategoryColor = (category: string): { fill: string; stroke: string } => {
        const colorMap: Record<string, { fill: string; stroke: string }> = {
          // Electronics (cyan/teal)
          'laptop': { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' },
          'monitor': { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' },
          'phone': { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' },
          'smartphone': { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' },
          'tablet': { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' },
          
          // Peripherals (yellow/lime)
          'gaming keyboard': { fill: 'rgba(234, 179, 8, 0.4)', stroke: 'rgba(234, 179, 8, 0.9)' },
          'keyboard': { fill: 'rgba(234, 179, 8, 0.4)', stroke: 'rgba(234, 179, 8, 0.9)' },
          'gaming mouse': { fill: 'rgba(234, 179, 8, 0.4)', stroke: 'rgba(234, 179, 8, 0.9)' },
          'mouse': { fill: 'rgba(234, 179, 8, 0.4)', stroke: 'rgba(234, 179, 8, 0.9)' },
          
          // Audio (purple)
          'headphones': { fill: 'rgba(168, 85, 247, 0.4)', stroke: 'rgba(168, 85, 247, 0.9)' },
          'microphone': { fill: 'rgba(168, 85, 247, 0.4)', stroke: 'rgba(168, 85, 247, 0.9)' },
          
          // Camera/Video (pink)
          'camera': { fill: 'rgba(236, 72, 153, 0.4)', stroke: 'rgba(236, 72, 153, 0.9)' },
          'webcam': { fill: 'rgba(236, 72, 153, 0.4)', stroke: 'rgba(236, 72, 153, 0.9)' },
          'tripod': { fill: 'rgba(236, 72, 153, 0.4)', stroke: 'rgba(236, 72, 153, 0.9)' },
          
          // Furniture (orange)
          'desk': { fill: 'rgba(249, 115, 22, 0.4)', stroke: 'rgba(249, 115, 22, 0.9)' },
          'chair': { fill: 'rgba(249, 115, 22, 0.4)', stroke: 'rgba(249, 115, 22, 0.9)' },
          
          // Accessories (green)
          'watch': { fill: 'rgba(34, 197, 94, 0.4)', stroke: 'rgba(34, 197, 94, 0.9)' },
          'glasses': { fill: 'rgba(34, 197, 94, 0.4)', stroke: 'rgba(34, 197, 94, 0.9)' },
          'sunglasses': { fill: 'rgba(34, 197, 94, 0.4)', stroke: 'rgba(34, 197, 94, 0.9)' },
          
          // Gaming (red)
          'game controller': { fill: 'rgba(239, 68, 68, 0.4)', stroke: 'rgba(239, 68, 68, 0.9)' },
          
          // Plants/Decor (emerald)
          'potted plant': { fill: 'rgba(16, 185, 129, 0.4)', stroke: 'rgba(16, 185, 129, 0.9)' },
          'plant': { fill: 'rgba(16, 185, 129, 0.4)', stroke: 'rgba(16, 185, 129, 0.9)' },
          
          // Stationery (blue)
          'notebook': { fill: 'rgba(59, 130, 246, 0.4)', stroke: 'rgba(59, 130, 246, 0.9)' },
        }
        
        return colorMap[category.toLowerCase()] || { fill: 'rgba(6, 182, 212, 0.4)', stroke: 'rgba(6, 182, 212, 0.9)' }
      }

      // Draw SAM segmentation masks with color coding
      for (const detection of detections) {
        const { track_id, class: className, bbox } = detection
        const product = trackingData.object_products[track_id]
        const category = product?.category || className
        const colors = getCategoryColor(category)
        
        // Check if this track has a segmentation mask
        if (product?.mask_url) {
          const maskUrl = `http://localhost:8000${product.mask_url}`
          
          // Load mask if not cached
          if (!maskCache[maskUrl]) {
            const img = new Image()
            img.crossOrigin = 'anonymous'
            img.src = maskUrl
            await new Promise((resolve) => {
              img.onload = resolve
              img.onerror = resolve
            })
            maskCache[maskUrl] = img
          }
          
          const maskImg = maskCache[maskUrl]
          if (maskImg.complete && maskImg.width > 0) {
            // Create temporary canvas for mask processing
            const tempCanvas = document.createElement('canvas')
            tempCanvas.width = canvas.width
            tempCanvas.height = canvas.height
            const tempCtx = tempCanvas.getContext('2d')
            
            if (tempCtx) {
              // Draw mask image
              tempCtx.drawImage(maskImg, 0, 0, canvas.width, canvas.height)
              const maskData = tempCtx.getImageData(0, 0, canvas.width, canvas.height)
              
              // Create colored overlay
              const overlayData = tempCtx.createImageData(canvas.width, canvas.height)
              
              // Parse colors
              const fillMatch = colors.fill.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/)
              const strokeMatch = colors.stroke.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/)
              
              if (fillMatch && strokeMatch) {
                const fillR = parseInt(fillMatch[1])
                const fillG = parseInt(fillMatch[2])
                const fillB = parseInt(fillMatch[3])
                const fillA = parseFloat(fillMatch[4])
                
                const strokeR = parseInt(strokeMatch[1])
                const strokeG = parseInt(strokeMatch[2])
                const strokeB = parseInt(strokeMatch[3])
                
                // Fill mask pixels with color
                for (let y = 0; y < canvas.height; y++) {
                  for (let x = 0; x < canvas.width; x++) {
                    const idx = (y * canvas.width + x) * 4
                    const maskValue = maskData.data[idx] // Grayscale value
                    
                    if (maskValue > 128) {
                      // Check if edge pixel
                      const isEdge = (
                        y > 0 && maskData.data[((y-1) * canvas.width + x) * 4] < 128 ||
                        y < canvas.height - 1 && maskData.data[((y+1) * canvas.width + x) * 4] < 128 ||
                        x > 0 && maskData.data[(y * canvas.width + (x-1)) * 4] < 128 ||
                        x < canvas.width - 1 && maskData.data[(y * canvas.width + (x+1)) * 4] < 128
                      )
                      
                      if (isEdge) {
                        // Draw border
                        overlayData.data[idx] = strokeR
                        overlayData.data[idx + 1] = strokeG
                        overlayData.data[idx + 2] = strokeB
                        overlayData.data[idx + 3] = 255
                      } else {
                        // Draw fill
                        overlayData.data[idx] = fillR
                        overlayData.data[idx + 1] = fillG
                        overlayData.data[idx + 2] = fillB
                        overlayData.data[idx + 3] = fillA * 255
                      }
                    }
                  }
                }
                
                // Draw the overlay
                tempCtx.putImageData(overlayData, 0, 0)
                ctx.drawImage(tempCanvas, 0, 0)
              }
            }
          }
        }
        
        // Draw label with matching category color
        const label = product?.category || className
        const labelHeight = 24
        
        // Calculate label position from bbox
        const scaleX = canvas.width / video.videoWidth
        const scaleY = canvas.height / video.videoHeight
        const labelX = bbox.x * scaleX
        const labelY = bbox.y * scaleY
        
        // Label background matching category color
        ctx.fillStyle = colors.stroke
        const textWidth = ctx.measureText(label).width
        const padding = 12
        const borderRadius = 6
        
        // Draw rounded rectangle for label
        const labelBoxX = labelX
        const labelBoxY = labelY - labelHeight - 4
        const labelWidth = textWidth + padding * 2
        
        ctx.beginPath()
        ctx.roundRect(labelBoxX, labelBoxY, labelWidth, labelHeight, borderRadius)
        ctx.fill()
        
        // Label text
        ctx.fillStyle = '#ffffff'
        ctx.font = '600 13px -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif'
        ctx.fillText(label, labelBoxX + padding, labelBoxY + 16)
      }
    }

    video.addEventListener('timeupdate', renderOverlays)
    return () => video.removeEventListener('timeupdate', renderOverlays)
  }, [trackingData])

  // Handle clicks on overlays
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!trackingData || !videoRef.current || !canvasRef.current) return

    const canvas = canvasRef.current
    const video = videoRef.current
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // Ignore clicks near the bottom (video controls area)
    if (y > rect.height - 50) {
      return // Click is on controls, ignore it
    }

    // Get current frame detections
    const currentTime = video.currentTime * 1000
    const timestamps = Object.keys(trackingData.tracks_by_frame).map(Number)
    const closestTimestamp = timestamps.reduce((prev, curr) => 
      Math.abs(curr - currentTime) < Math.abs(prev - currentTime) ? curr : prev
    )

    const detections = trackingData.tracks_by_frame[closestTimestamp] || []

    // Check if click is inside any bounding box
    const scaleX = canvas.width / video.videoWidth
    const scaleY = canvas.height / video.videoHeight

    for (const detection of detections) {
      const { bbox, track_id } = detection
      const boxX = bbox.x * scaleX
      const boxY = bbox.y * scaleY
      const boxWidth = bbox.width * scaleX
      const boxHeight = bbox.height * scaleY

      if (x >= boxX && x <= boxX + boxWidth && y >= boxY && y <= boxY + boxHeight) {
        // Clicked on this object
        const product = trackingData.object_products[track_id]
        if (product?.product?.buy_url) {
          // Redirect to buy page
          window.open(product.product.buy_url, '_blank')
        }
        break
      }
    }
  }


  const updateCanvasSize = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    // Set canvas internal resolution to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    // Detect aspect ratio
    if (video.videoWidth && video.videoHeight) {
      const aspectRatio = video.videoWidth / video.videoHeight
      setVideoAspectRatio(aspectRatio > 1 ? 'horizontal' : 'vertical')
    }
    
    // Match canvas display size to actual video element display size
    const videoRect = video.getBoundingClientRect()
    const containerRect = containerRef.current?.getBoundingClientRect()
    
    canvas.style.width = `${videoRect.width}px`
    canvas.style.height = `${videoRect.height}px`
    
    // Position canvas to match video element within container
    if (containerRect) {
      const leftOffset = videoRect.left - containerRect.left
      const topOffset = videoRect.top - containerRect.top
      canvas.style.left = `${leftOffset}px`
      canvas.style.top = `${topOffset}px`
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {!videoUrl ? (
        <div className="bg-white rounded-3xl p-16 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300">
          <label className="flex flex-col items-center cursor-pointer">
            <Upload className="w-20 h-20 text-gray-400 mb-6" />
            <span className="text-xl text-gray-900 mb-2 font-medium">
              {isUploading ? 'Uploading...' : 'Upload a video'}
            </span>
            <span className="text-base text-gray-500 font-light">
              MP4, MOV, or WebM (max 100MB)
            </span>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="bg-white rounded-3xl overflow-hidden shadow-lg">
          {isProcessing && (
            <div className="bg-gray-50 p-6 border-b border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-700 text-base font-medium">
                  {processingMessage}
                </span>
                <span className="text-gray-500 text-base font-light">
                  {processingProgress.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${processingProgress}%` }}
                />
              </div>
              {processingLogs.length > 0 && (
                <div className="mt-4 bg-white rounded-lg p-4 border border-gray-200">
                  <div className="text-sm font-medium text-gray-700 mb-2">Processing Log:</div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {processingLogs.slice(-10).map((log, idx) => (
                      <div key={idx} className="text-xs text-gray-600 font-mono">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div 
            className="relative bg-black flex items-center justify-center" 
            ref={containerRef}
            style={{
              maxHeight: videoAspectRatio === 'vertical' ? '80vh' : 'none'
            }}
          >
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              className={`rounded-b-3xl ${
                videoAspectRatio === 'vertical' 
                  ? 'h-full max-h-[80vh] w-auto' 
                  : 'w-full'
              }`}
              onLoadedMetadata={updateCanvasSize}
              onPlay={updateCanvasSize}
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
            />
            {/* Clickable overlay divs for each detection */}
            {trackingData && videoRef.current && currentDetections.map((detection: any) => {
              const video = videoRef.current!
              const scaleX = (containerRef.current?.offsetWidth || video.videoWidth) / video.videoWidth
              const scaleY = (containerRef.current?.offsetHeight || video.videoHeight) / video.videoHeight
              
              const x = detection.bbox.x * scaleX
              const y = detection.bbox.y * scaleY
              const width = detection.bbox.width * scaleX
              const height = detection.bbox.height * scaleY
              
              const product = trackingData.object_products[detection.track_id]
              
              return (
                <div
                  key={detection.track_id}
                  className="absolute cursor-pointer hover:bg-blue-500 hover:bg-opacity-10 transition-all duration-200"
                  style={{
                    left: `${x}px`,
                    top: `${y}px`,
                    width: `${width}px`,
                    height: `${height}px`,
                  }}
                  onClick={() => {
                    if (product?.product?.buy_url) {
                      window.open(product.product.buy_url, '_blank')
                    }
                  }}
                  title={product?.category || detection.class}
                />
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
