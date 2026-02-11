"""Real product search service using Google Shopping API."""

import os
import requests
from typing import List, Optional
from app.schemas.product import Product
from app.core.config import settings

class ProductSearchService:
    """Search for real products on the internet using Google Shopping."""
    
    def __init__(self):
        # Get API key from environment
        self.serpapi_key = os.getenv("SERPAPI_API_KEY", "")
        self.use_serpapi = bool(self.serpapi_key)
        
    async def search_products(
        self,
        category: str,
        top_k: int = 5
    ) -> List[Product]:
        """
        Search for products online based on the classified object category.
        
        Args:
            category: The object category (e.g., "sneakers", "hoodie")
            top_k: Number of results to return
            
        Returns:
            List of Product objects with real buying links
        """
        
        if self.use_serpapi:
            return await self._search_with_serpapi(category, top_k)
        else:
            # Fallback: use mock data if no API key
            return await self._mock_search(category, top_k)
    
    async def _search_with_serpapi(self, category: str, top_k: int) -> List[Product]:
        """Search using SerpAPI (Google Shopping)."""
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_shopping",
                "q": category,
                "api_key": self.serpapi_key,
                "num": top_k
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            products = []
            shopping_results = data.get("shopping_results", [])
            
            for result in shopping_results[:top_k]:
                product = Product(
                    product_id=result.get("product_id", ""),
                    title=result.get("title", "Unknown Product"),
                    brand=result.get("source", ""),
                    price=self._extract_price(result.get("price", "")),
                    currency="USD",
                    image_url=result.get("thumbnail", ""),
                    buy_url=result.get("link", ""),
                    category=category,
                    confidence=0.85  # High confidence for real search results
                )
                products.append(product)
            
            return products
            
        except Exception as e:
            print(f"SerpAPI search failed: {e}")
            return await self._mock_search(category, top_k)
    
    async def _mock_search(self, category: str, top_k: int) -> List[Product]:
        """Fallback mock search when no API key is available."""
        
        # Mock product data based on category
        mock_products = {
            "sneakers": [
                {
                    "title": f"Classic {category.title()}",
                    "brand": "Nike",
                    "price": 89.99,
                    "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                    "buy_url": f"https://www.google.com/search?q={category}+buy+online&tbm=shop"
                },
                {
                    "title": f"Premium {category.title()}",
                    "brand": "Adidas",
                    "price": 110.00,
                    "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772",
                    "buy_url": f"https://www.google.com/search?q={category}+buy+online&tbm=shop"
                }
            ],
            "hoodie": [
                {
                    "title": f"Comfortable {category.title()}",
                    "brand": "Champion",
                    "price": 65.00,
                    "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7",
                    "buy_url": f"https://www.google.com/search?q={category}+buy+online&tbm=shop"
                }
            ],
            "jeans": [
                {
                    "title": f"Denim {category.title()}",
                    "brand": "Levi's",
                    "price": 79.99,
                    "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d",
                    "buy_url": f"https://www.google.com/search?q={category}+buy+online&tbm=shop"
                }
            ]
        }
        
        # Get mock products for this category or use generic
        category_products = mock_products.get(category, [
            {
                "title": f"{category.title()}",
                "brand": "Generic Brand",
                "price": 50.00,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
                "buy_url": f"https://www.google.com/search?q={category}+buy+online&tbm=shop"
            }
        ])
        
        products = []
        for i, mock_data in enumerate(category_products[:top_k]):
            product = Product(
                product_id=f"mock-{category}-{i}",
                title=mock_data["title"],
                brand=mock_data["brand"],
                price=mock_data["price"],
                currency="USD",
                image_url=mock_data["image_url"],
                buy_url=mock_data["buy_url"],
                category=category,
                confidence=0.70  # Lower confidence for mock data
            )
            products.append(product)
        
        return products
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price from string like '$89.99'."""
        try:
            # Remove currency symbols and convert to float
            price_clean = price_str.replace("$", "").replace(",", "").strip()
            return float(price_clean)
        except:
            return 0.0
