#!/usr/bin/env python3
"""
Enhanced Web Scraper for Oral B iO3 Product Information
This script visits each URL from the JSON file and extracts pricing, offers, and stock information
with human-like browsing behavior using Playwright. Includes screenshot capture and comprehensive text extraction.
"""

import json
import asyncio
import random
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
import base64

from playwright.async_api import async_playwright, Browser, Page


class ProductScrapingAgent:
    """Web scraping agent for extracting product information from e-commerce websites."""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.data = self.load_json_data()
        self.results = []
        self.browser = None
        self.page = None
        self.screenshots_dir = "screenshots"
        self.texts_dir = "extracted_texts"
        
        # Create directories for screenshots and texts
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.texts_dir, exist_ok=True)
        
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
        """Extract price information from the page with enhanced selectors."""
        price_info = {
            'current_price': None,
            'original_price': None,
            'discount_percentage': None,
            'currency': '₹',
            'price_elements_found': []
        }
        
        try:
            # Enhanced price selectors for different e-commerce sites
            price_selectors = [
                # Amazon selectors
                '.a-price-whole', '.a-offscreen', '.a-price-range', '.a-price',
                '.a-price .a-offscreen', '.a-price-range .a-offscreen',
                '.a-price-whole', '.a-price-symbol', '.a-price-fraction',
                '.a-price .a-text-strike', '.a-price-range .a-text-strike',
                
                # Flipkart selectors
                '.price-current', '.current-price', '.price-now', '.price-value',
                '.selling-price', '.final-price', '.price-box .price',
                '.price-original', '.original-price', '.was-price',
                
                # Myntra selectors
                '.pdp-price', '.pdp-discount', '.pdp-mrp', '.pdp-selling-price',
                '.price', '.product-price', '.discount-price',
                
                # Generic selectors
                '.price', '.product-price', '.selling-price', '.final-price',
                '.price-box .price', '.price-current', '.price-now', '.price-value',
                '[data-testid="price"]', '.price-current', '.price-now',
                '.price-original', '.original-price', '.was-price', '.strikethrough',
                '.old-price', '.price-before', '.discount-price', '.sale-price',
                
                # Additional selectors for various sites
                '.price-amount', '.price-value', '.current-price', '.sale-price',
                '.price-display', '.product-price-value', '.price-text',
                '.price-container .price', '.price-wrapper .price',
                '.product-details .price', '.product-info .price',
                '.main-price', '.primary-price', '.offer-price'
            ]
            
            # Extract current price
            for selector in price_selectors:
                try:
                    price_elements = await page.query_selector_all(selector)
                    for element in price_elements:
                        price_text = await element.text_content()
                        if price_text and price_text.strip():
                            # Extract numeric price
                            price_match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', price_text.strip())
                            if price_match:
                                price_info['current_price'] = price_match.group()
                                price_info['price_elements_found'].append({
                                    'selector': selector,
                                    'text': price_text.strip(),
                                    'type': 'current'
                                })
                                break
                    if price_info['current_price']:
                        break
                except:
                    continue
            
            # Try to find original price (crossed out)
            original_price_selectors = [
                '.price-original', '.original-price', '.was-price', '.strikethrough',
                '.a-text-strike', '.price-was', '.old-price', '.price-before',
                '.a-price .a-text-strike', '.a-price-range .a-text-strike',
                '.mrp', '.list-price', '.regular-price', '.before-price',
                '.crossed-price', '.strike-price', '.old-price-text'
            ]
            
            for selector in original_price_selectors:
                try:
                    original_elements = await page.query_selector_all(selector)
                    for element in original_elements:
                        original_text = await element.text_content()
                        if original_text and original_text.strip():
                            price_match = re.search(r'[₹$€£]\s*[\d,]+\.?\d*', original_text.strip())
                            if price_match:
                                price_info['original_price'] = price_match.group()
                                price_info['price_elements_found'].append({
                                    'selector': selector,
                                    'text': original_text.strip(),
                                    'type': 'original'
                                })
                                break
                    if price_info['original_price']:
                        break
                except:
                    continue
            
            # Calculate discount percentage if both prices are available
            if price_info['current_price'] and price_info['original_price']:
                try:
                    current = float(re.sub(r'[₹$€£,\s]', '', price_info['current_price']))
                    original = float(re.sub(r'[₹$€£,\s]', '', price_info['original_price']))
                    if original > current:
                        discount = ((original - current) / original) * 100
                        price_info['discount_percentage'] = f"{discount:.1f}%"
                except:
                    pass
            
        except Exception as e:
            print(f"Error extracting price info: {e}")
        
        return price_info
    
    async def extract_offers(self, page: Page) -> List[str]:
        """Extract available offers and promotions with enhanced selectors."""
        offers = []
        
        try:
            # Enhanced offer selectors for different e-commerce sites
            offer_selectors = [
                # Amazon selectors
                '.a-badge-text', '.a-color-price', '.a-size-base',
                '.promotional-offer', '.deal-badge', '.savings-badge',
                '.a-offer', '.a-promo', '.a-deal', '.a-savings',
                
                # Flipkart selectors
                '.offer', '.promotion', '.discount', '.deal', '.savings',
                '.coupon', '.promo', '.special-offer', '.limited-time',
                '.badge', '.tag', '.label', '.offer-text', '.promo-text',
                
                # Myntra selectors
                '.pdp-offer', '.pdp-discount', '.pdp-promo', '.pdp-deal',
                '.offer-badge', '.discount-badge', '.promo-badge',
                
                # Generic selectors
                '.discount-text', '.deal-text', '.savings-text',
                '.offer-banner', '.promo-banner', '.deal-banner',
                '.special-offer-text', '.limited-time-offer',
                '.coupon-code', '.promo-code', '.discount-code',
                '.offer-message', '.promo-message', '.deal-message',
                '.savings-message', '.offer-highlight', '.promo-highlight',
                '.deal-highlight', '.savings-highlight',
                
                # Additional selectors
                '.offer-tag', '.promo-tag', '.deal-tag', '.savings-tag',
                '.offer-label', '.promo-label', '.deal-label', '.savings-label',
                '.offer-badge-text', '.promo-badge-text', '.deal-badge-text',
                '.savings-badge-text', '.offer-info', '.promo-info',
                '.deal-info', '.savings-info'
            ]
            
            for selector in offer_selectors:
                try:
                    offer_elements = await page.query_selector_all(selector)
                    for element in offer_elements:
                        offer_text = await element.text_content()
                        if offer_text and offer_text.strip():
                            # Clean and validate offer text
                            clean_text = offer_text.strip()
                            if len(clean_text) > 3 and len(clean_text) < 300:
                                offers.append(clean_text)
                except:
                    continue
            
            # Remove duplicates and filter meaningful offers
            offers = list(set(offers))
            offers = [offer for offer in offers if len(offer) > 5 and len(offer) < 200]
            
        except Exception as e:
            print(f"Error extracting offers: {e}")
        
        return offers[:10]  # Limit to top 10 offers
    
    async def extract_page_text(self, page: Page) -> Dict[str, Any]:
        """Extract comprehensive text content from the page."""
        text_data = {
            'page_title': None,
            'meta_description': None,
            'product_title': None,
            'product_description': None,
            'all_text': None,
            'visible_text': None,
            'price_related_text': [],
            'offer_related_text': [],
            'stock_related_text': []
        }
        
        try:
            # Get page title
            text_data['page_title'] = await page.title()
            
            # Get meta description
            try:
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    text_data['meta_description'] = await meta_desc.get_attribute('content')
            except:
                pass
            
            # Get product title
            product_title_selectors = [
                'h1', '.product-title', '.product-name', '.pdp-title',
                '.product-heading', '.item-title', '.product-name-text',
                '.a-size-large', '.a-size-medium', '.product-title-text'
            ]
            
            for selector in product_title_selectors:
                try:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title_text = await title_element.text_content()
                        if title_text and title_text.strip():
                            text_data['product_title'] = title_text.strip()
                            break
                except:
                    continue
            
            # Get product description
            description_selectors = [
                '.product-description', '.product-details', '.product-info',
                '.pdp-description', '.item-description', '.product-summary',
                '.a-size-base', '.product-details-text', '.description-text'
            ]
            
            for selector in description_selectors:
                try:
                    desc_element = await page.query_selector(selector)
                    if desc_element:
                        desc_text = await desc_element.text_content()
                        if desc_text and desc_text.strip():
                            text_data['product_description'] = desc_text.strip()
                            break
                except:
                    continue
            
            # Get all visible text
            try:
                text_data['visible_text'] = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        let text = '';
                        let node;
                        while (node = walker.nextNode()) {
                            if (node.parentElement.offsetParent !== null) {
                                text += node.textContent + ' ';
                            }
                        }
                        return text.trim();
                    }
                """)
            except:
                pass
            
            # Get all text content
            try:
                text_data['all_text'] = await page.text_content('body')
            except:
                pass
            
            # Extract price-related text
            try:
                price_elements = await page.query_selector_all('.price, .cost, .amount, .value, [class*="price"], [class*="cost"], [class*="amount"]')
                for element in price_elements:
                    text = await element.text_content()
                    if text and text.strip():
                        text_data['price_related_text'].append(text.strip())
            except:
                pass
            
            # Extract offer-related text
            try:
                offer_elements = await page.query_selector_all('.offer, .promo, .deal, .discount, [class*="offer"], [class*="promo"], [class*="deal"], [class*="discount"]')
                for element in offer_elements:
                    text = await element.text_content()
                    if text and text.strip():
                        text_data['offer_related_text'].append(text.strip())
            except:
                pass
            
            # Extract stock-related text
            try:
                stock_elements = await page.query_selector_all('.stock, .availability, .inventory, [class*="stock"], [class*="availability"], [class*="inventory"]')
                for element in stock_elements:
                    text = await element.text_content()
                    if text and text.strip():
                        text_data['stock_related_text'].append(text.strip())
            except:
                pass
            
        except Exception as e:
            print(f"Error extracting page text: {e}")
        
        return text_data
    
    async def take_screenshot(self, page: Page, url_info: Dict) -> str:
        """Take a screenshot of the page and save it."""
        try:
            # Create a safe filename
            safe_store_name = re.sub(r'[^\w\-_\.]', '_', url_info['store_name'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_store_name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take full page screenshot
            await page.screenshot(path=filepath, full_page=True)
            
            # Also take a viewport screenshot
            viewport_filename = f"{safe_store_name}_{timestamp}_viewport.png"
            viewport_filepath = os.path.join(self.screenshots_dir, viewport_filename)
            await page.screenshot(path=viewport_filepath, full_page=False)
            
            return filepath
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    async def save_page_text(self, text_data: Dict, url_info: Dict) -> str:
        """Save extracted text data to a file."""
        try:
            # Create a safe filename
            safe_store_name = re.sub(r'[^\w\-_\.]', '_', url_info['store_name'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_store_name}_{timestamp}.json"
            filepath = os.path.join(self.texts_dir, filename)
            
            # Save text data as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(text_data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            print(f"Error saving page text: {e}")
            return None
    
    async def check_stock_status(self, page: Page) -> Dict[str, Any]:
        """Check if the product is in stock."""
        stock_info = {
            'in_stock': False,
            'stock_status': 'Unknown',
            'stock_message': None
        }
        
        try:
            # Check for "Add to Cart" button as stock indicator
            add_to_cart_selectors = [
                'button[data-testid="add-to-cart"]', '.add-to-cart', '.add-to-basket',
                'button:has-text("Add to Cart")', 'button:has-text("Add to Bag")',
                'button:has-text("Buy Now")', 'button:has-text("Purchase")',
                '.buy-button', '.purchase-button', '.order-button',
                '#add-to-cart-button', '.a-button-primary',
                'button:has-text("Add to Cart")', 'button:has-text("Buy now")',
                'button:has-text("Add to basket")', 'button:has-text("Add to cart")'
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
                '.product-status', '.availability-text', '.stock-text',
                '.a-size-medium', '.a-color-success', '.a-color-error'
            ]
            
            for selector in stock_message_selectors:
                try:
                    message_element = await page.query_selector(selector)
                    if message_element:
                        message_text = await message_element.text_content()
                        if message_text:
                            stock_info['stock_message'] = message_text.strip()
                            if any(word in message_text.lower() for word in ['in stock', 'available', 'ready', 'add to cart']):
                                stock_info['in_stock'] = True
                                stock_info['stock_status'] = 'In Stock'
                            elif any(word in message_text.lower() for word in ['out of stock', 'unavailable', 'sold out', 'not available']):
                                stock_info['in_stock'] = False
                                stock_info['stock_status'] = 'Out of Stock'
                            break
                except:
                    continue
            
        except Exception as e:
            print(f"Error checking stock status: {e}")
        
        return stock_info
    
    async def scrape_product_page(self, url_info: Dict) -> Dict[str, Any]:
        """Scrape a single product page with comprehensive data extraction."""
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
            'product_images': [],
            'screenshot_path': None,
            'text_data_path': None,
            'page_text': {},
            'expected_data': {
                'expected_price': url_info['expected_price'],
                'color': url_info['color'],
                'packaging_type': url_info['packaging_type'],
                'product_condition': url_info['product_condition'],
                'shipping': url_info['shipping'],
                'offer_title': url_info['offer_title']
            }
        }
        
        try:
            print(f"Scraping: {url_info['store_name']} - {url_info['url']}")
            
            # Navigate to the page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.page.goto(url_info['url'], wait_until='networkidle', timeout=30000)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Retry {attempt + 1} for {url_info['store_name']}")
                    await self.human_like_delay(2, 4)
            
            await self.human_like_delay(2, 4)
            
            # Get page title
            result['page_title'] = await self.page.title()
            
            # Scroll the page human-like
            await self.scroll_page_human_like(self.page)
            
            # Extract comprehensive text data
            result['page_text'] = await self.extract_page_text(self.page)
            
            # Extract price information
            result['price_info'] = await self.extract_price_info(self.page, url_info['store_name'])
            
            # Extract offers
            result['offers'] = await self.extract_offers(self.page)
            
            # Check stock status
            result['stock_info'] = await self.check_stock_status(self.page)
            
            # Try to extract product images
            try:
                image_selectors = [
                    'img[src*="product"]', 'img[alt*="product"]', 
                    '.product-image img', '.main-image img',
                    '.a-dynamic-image', '.a-image-wrapper img',
                    '.product-photo img', '.gallery-image img',
                    '.pdp-image img', '.item-image img',
                    '.product-gallery img', '.image-gallery img'
                ]
                image_elements = []
                for selector in image_selectors:
                    elements = await self.page.query_selector_all(selector)
                    image_elements.extend(elements)
                
                for img in image_elements[:5]:  # Limit to first 5 images
                    src = await img.get_attribute('src')
                    if src and src.startswith('http'):
                        result['product_images'].append(src)
            except:
                pass
            
            # Take screenshot
            result['screenshot_path'] = await self.take_screenshot(self.page, url_info)
            
            # Save text data
            result['text_data_path'] = await self.save_page_text(result['page_text'], url_info)
            
            result['success'] = True
            print(f"✓ Successfully scraped {url_info['store_name']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Error scraping {url_info['store_name']}: {e}")
        
        return result
    
    async def run_scraping(self):
        """Run the complete scraping process."""
        print("Starting Product Scraping Agent for Oral B iO3")
        print("=" * 60)
        
        # Extract all URLs
        urls = self.extract_all_urls()
        print(f"Found {len(urls)} URLs to scrape")
        
        # Initialize browser with enhanced configuration
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Disable images for faster loading
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Create a new page with realistic user agent and headers
        self.page = await self.browser.new_page()
        
        # Set viewport to a common desktop size
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Set extra HTTP headers
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Block only unnecessary resources for faster loading (keep CSS and JS for proper rendering)
        await self.page.route("**/*.{woff,woff2,ttf,eot}", lambda route: route.abort())
        
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
        output_file = f"scraping_results_{timestamp}.json"
        
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
    json_file_path = "Oral B iO3.json"
    
    if not Path(json_file_path).exists():
        print(f"Error: JSON file not found at {json_file_path}")
        return
    
    agent = ProductScrapingAgent(json_file_path)
    await agent.run_scraping()


if __name__ == "__main__":
    asyncio.run(main())

