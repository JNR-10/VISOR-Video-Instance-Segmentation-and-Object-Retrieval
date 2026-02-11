'use client'

import { useState } from 'react'
import VideoPlayer from '@/components/VideoPlayer'
import ProductDrawer from '@/components/ProductDrawer'
import { Product } from '@/types'

export default function Home() {
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([])
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleProductsFound = (products: Product[]) => {
    setSelectedProducts(products)
    setIsDrawerOpen(true)
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-6 py-12 max-w-7xl">
        <header className="text-center mb-12">
          <h1 className="text-6xl font-semibold text-gray-900 mb-3 tracking-tight">
            VISOR
          </h1>
          <p className="text-gray-600 text-xl font-light">
            Video Instance Segmentation & Object Retrieval
          </p>
          <p className="text-gray-500 text-base mt-3 font-light">
            Click on any object in the video to find similar products
          </p>
        </header>

        <div className="flex flex-col lg:flex-row gap-6 items-start">
          <div className="flex-1 w-full">
            <VideoPlayer onProductsFound={handleProductsFound} />
          </div>

          <ProductDrawer
            products={selectedProducts}
            isOpen={isDrawerOpen}
            onClose={() => setIsDrawerOpen(false)}
          />
        </div>
      </div>
    </main>
  )
}
