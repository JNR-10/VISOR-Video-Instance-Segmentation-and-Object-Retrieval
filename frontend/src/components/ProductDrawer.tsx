'use client'

import { X, ExternalLink, ShoppingCart } from 'lucide-react'
import { Product } from '@/types'
import { formatPrice, formatConfidence } from '@/lib/utils'
import api from '@/lib/api'

interface ProductDrawerProps {
  products: Product[]
  isOpen: boolean
  onClose: () => void
}

export default function ProductDrawer({ products, isOpen, onClose }: ProductDrawerProps) {
  const handleProductClick = async (product: Product) => {
    await api.logEvent({
      event_type: 'product_click',
      product_id: product.product_id,
    })
    window.open(product.buy_url, '_blank')
  }

  if (!isOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
        onClick={onClose}
      />
      
      <div className={`
        fixed lg:relative
        top-0 right-0 h-full
        w-full sm:w-96
        bg-slate-800 
        shadow-2xl
        transform transition-transform duration-300
        z-50
        ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 border-b border-slate-700">
            <h2 className="text-xl font-bold text-white">Similar Products</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {products.length === 0 ? (
              <div className="text-center py-12">
                <ShoppingCart className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No products found</p>
                <p className="text-slate-500 text-sm mt-2">
                  Click on an object in the video to find similar products
                </p>
              </div>
            ) : (
              products.map((product) => (
                <div
                  key={product.product_id}
                  className="bg-slate-700 rounded-lg overflow-hidden hover:bg-slate-600 transition-colors cursor-pointer"
                  onClick={() => handleProductClick(product)}
                >
                  <div className="aspect-square relative">
                    <img
                      src={product.image_url}
                      alt={product.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                      {formatConfidence(product.confidence)}
                    </div>
                  </div>
                  
                  <div className="p-4">
                    <h3 className="text-white font-semibold mb-1 line-clamp-2">
                      {product.title}
                    </h3>
                    
                    {product.brand && (
                      <p className="text-slate-400 text-sm mb-2">{product.brand}</p>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <span className="text-purple-400 font-bold text-lg">
                        {formatPrice(product.price, product.currency)}
                      </span>
                      <ExternalLink className="w-4 h-4 text-slate-400" />
                    </div>
                    
                    {product.category && (
                      <span className="inline-block mt-2 text-xs bg-slate-600 text-slate-300 px-2 py-1 rounded">
                        {product.category}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  )
}
