import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price?: number, currency: string = 'USD'): string {
  if (price === undefined || price === null) return 'N/A'
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(price)
}

export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(0)}%`
}
