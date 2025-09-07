#!/usr/bin/env python3
"""
Agno Agent for Oral B iO3 Product Scraping
This agent visits each URL from the JSON file and extracts pricing, offers, and stock information
with human-like browsing behavior.
"""

import json
import asyncio
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from agno import Agent, Task, Tool
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import re


class ProductScrapingAgent:
    """Agno agent for scraping product information from e-commerce websites."""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.data = self.load_json_data()
        self.results = []
        self.browser = None
        self.page = None
        
    def load_json_data(self) -> Dict:
        """Load the JSON data containing product URLs."""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_all_urls(self) -> List[Dict]:
        """Extract all URLs from the JSON data with their metadata."""
        urls = []
        
        for variant in self.data.get('variants', []):
            for store_link in variant.get('store_links', []):
                url_info = {
                    'url': store_link.get('url'),
                    'store_name': store_link.get('name'),
                    'expected_price': store_link.get('price'),
                    'color': variant.get('color'),
                    'packaging_type': variant.get('packaging_type'),
                    'product_condition': store_link.get('product_condition'),
                    'shipping': store_link.get('shipping'),
                    'offer_title': store_link.get('offer_title')
                }
                if url_info['url']:
                    urls.append(url_info)
        
        return urls
    
    async def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add human-like random delays between actions."""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def scroll_page_human_like(self, page: Page):
        """Scroll the page in a human-like manner."""
        # Random scroll patterns
        scroll_actions = random.randint(2, 5)
        for _ in range(scroll_actions):
            scroll_distance = random.randint(200, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await self.human_like_delay(0.5, 1.5)
        
        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await self.human_like_delay(0.5, 1.0)
    
    async def extract_price_info(self, page: Page, store_name: str) -> Dict[str, Any]:
        """Extract price information from the page."""
        price_info = {
            'current_price': None,
            'original_price': None,
            'discount_percentage': None,
            'currency': '₹'
        }
        
        try:
            # Common price selectors for different e-commerce sites
            price_selectors = [
                '.price-current', '.current-price', '.price-now', '.price-value',
                '.a-price-whole', '.a-offscreen', '.a-price-range', '.a-price',
                '.price', '.product-price', '.selling-price', '.final-price',
                '.price-box .price', '.price-current', '.price-now', '.price-value',
                '[data-testid="price"]', '.price-current', '.price-now'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await page.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        if price_text:
                            # Extract numeric price
                            price_match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', price_text)
                            if price_match:
                                price_info['current_price'] = price_match.group()
                                break
                except:
                    continue
            
            # Try to find original price (crossed out)
            original_price_selectors = [
                '.price-original', '.original-price', '.was-price', '.strikethrough',
                '.a-text-strike', '.price-was', '.old-price', '.price-before'
            ]
            
            for selector in original_price_selectors:
                try:
                    original_element = await page.query_selector(selector)
                    if original_element:
                        original_text = await original_element.text_content()
                        if original_text:
                            price_match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', original_text)
                            if price_match:
                                price_info['original_price'] = price_match.group()
                                break
                except:
                    continue
            
        except Exception as e:
            print(f"Error extracting price info: {e}")
        
        return price_info
    
    async def extract_offers(self, page: Page) -> List[str]:
        """Extract available offers and promotions."""
        offers = []
        
        try:
            # Common offer selectors
            offer_selectors = [
                '.offer', '.promotion', '.discount', '.deal', '.savings',
                '.coupon', '.promo', '.special-offer', '.limited-time',
                '.badge', '.tag', '.label', '.offer-text', '.promo-text',
                '.discount-text', '.deal-text', '.savings-text'
            ]
            
            for selector in offer_selectors:
                try:
                    offer_elements = await page.query_selector_all(selector)
                    for element in offer_elements:
                        offer_text = await element.text_content()
                        if offer_text and offer_text.strip():
                            offers.append(offer_text.strip())
                except:
                    continue
            
            # Remove duplicates and filter meaningful offers
            offers = list(set(offers))
            offers = [offer for offer in offers if len(offer) > 5 and len(offer) < 200]
            
        except Exception as e:
            print(f"Error extracting offers: {e}")
        
        return offers[:5]  # Limit to top 5 offers
    
    async def check_stock_status(self, page: Page) -> Dict[str, Any]:
        """Check if the product is in stock."""
        stock_info = {
            'in_stock': False,
            'stock_status': 'Unknown',
            'stock_message': None
        }
        
        try:
            # Common stock status selectors
            stock_selectors = [
                '.stock-status', '.availability', '.in-stock', '.out-of-stock',
                '.stock', '.inventory', '.availability-status', '.product-availability',
                '.add-to-cart', '.buy-now', '.purchase', '.order-now'
            ]
            
            # Check for "Add to Cart" button as stock indicator
            add_to_cart_selectors = [
                'button[data-testid="add-to-cart"]', '.add-to-cart', '.add-to-basket',
                'button:has-text("Add to Cart")', 'button:has-text("Add to Bag")',
                'button:has-text("Buy Now")', 'button:has-text("Purchase")',
                '.buy-button', '.purchase-button', '.order-button'
            ]
            
            for selector in add_to_cart_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        if is_visible and is_enabled:
                            stock_info['in_stock'] = True
                            stock_info['stock_status'] = 'In Stock'
                            break
                except:
                    continue
            
            # Check for explicit stock messages
            stock_message_selectors = [
                '.stock-message', '.availability-message', '.inventory-message',
                '.product-status', '.availability-text', '.stock-text'
            ]
            
            for selector in stock_message_selectors:
                try:
                    message_element = await page.query_selector(selector)
                    if message_element:
                        message_text = await message_element.text_content()
                        if message_text:
                            stock_info['stock_message'] = message_text.strip()
                            if any(word in message_text.lower() for word in ['in stock', 'available', 'ready']):
                                stock_info['in_stock'] = True
                                stock_info['stock_status'] = 'In Stock'
                            elif any(word in message_text.lower() for word in ['out of stock', 'unavailable', 'sold out']):
                                stock_info['in_stock'] = False
                                stock_info['stock_status'] = 'Out of Stock'
                            break
                except:
                    continue
            
        except Exception as e:
            print(f"Error checking stock status: {e}")
        
        return stock_info
    
    async def scrape_product_page(self, url_info: Dict) -> Dict[str, Any]:
        """Scrape a single product page."""
        result = {
            'url': url_info['url'],
            'store_name': url_info['store_name'],
            'scraped_at': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'price_info': {},
            'offers': [],
            'stock_info': {},
            'page_title': None,
            'product_images': []
        }
        
        try:
            print(f"Scraping: {url_info['store_name']} - {url_info['url']}")
            
            # Navigate to the page
            await self.page.goto(url_info['url'], wait_until='networkidle', timeout=30000)
            await self.human_like_delay(2, 4)
            
            # Get page title
            result['page_title'] = await self.page.title()
            
            # Scroll the page human-like
            await self.scroll_page_human_like(self.page)
            
            # Extract price information
            result['price_info'] = await self.extract_price_info(self.page, url_info['store_name'])
            
            # Extract offers
            result['offers'] = await self.extract_offers(self.page)
            
            # Check stock status
            result['stock_info'] = await self.check_stock_status(self.page)
            
            # Try to extract product images
            try:
                image_elements = await self.page.query_selector_all('img[src*="product"], img[alt*="product"], .product-image img, .main-image img')
                for img in image_elements[:3]:  # Limit to first 3 images
                    src = await img.get_attribute('src')
                    if src:
                        result['product_images'].append(src)
            except:
                pass
            
            result['success'] = True
            print(f"✓ Successfully scraped {url_info['store_name']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Error scraping {url_info['store_name']}: {e}")
        
        return result
    
    async def run_scraping(self):
        """Run the complete scraping process."""
        print("Starting Agno Agent for Oral B iO3 Product Scraping")
        print("=" * 60)
        
        # Extract all URLs
        urls = self.extract_all_urls()
        print(f"Found {len(urls)} URLs to scrape")
        
        # Initialize browser
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create a new page with realistic user agent
        self.page = await self.browser.new_page()
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        try:
            # Process each URL
            for i, url_info in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing: {url_info['store_name']}")
                
                result = await self.scrape_product_page(url_info)
                self.results.append(result)
                
                # Add delay between requests
                if i < len(urls):
                    await self.human_like_delay(3, 6)
            
        finally:
            await self.browser.close()
            await playwright.stop()
        
        # Save results
        await self.save_results()
        
        print("\n" + "=" * 60)
        print("Scraping completed!")
        print(f"Successfully scraped: {sum(1 for r in self.results if r['success'])}/{len(self.results)} URLs")
    
    async def save_results(self):
        """Save the scraping results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"oralb-campaign/scraping_results_{timestamp}.json"
        
        output_data = {
            'scraping_metadata': {
                'total_urls': len(self.results),
                'successful_scrapes': sum(1 for r in self.results if r['success']),
                'failed_scrapes': sum(1 for r in self.results if not r['success']),
                'scraping_date': datetime.now().isoformat(),
                'source_file': self.json_file_path
            },
            'results': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_file}")


async def main():
    """Main function to run the scraping agent."""
    json_file_path = "oralb-campaign/Oral B iO3.json"
    
    if not Path(json_file_path).exists():
        print(f"Error: JSON file not found at {json_file_path}")
        return
    
    agent = ProductScrapingAgent(json_file_path)
    await agent.run_scraping()


if __name__ == "__main__":
    asyncio.run(main())
