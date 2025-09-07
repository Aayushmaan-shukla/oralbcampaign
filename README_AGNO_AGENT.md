# Agno Agent for Oral B iO3 Product Scraping

This project uses the Agno framework to create an intelligent web scraping agent that visits each URL from the `Oral B iO3.json` file and extracts pricing, offers, and stock information with human-like browsing behavior.

## Features

- **Human-like Browsing**: Random delays, scrolling patterns, and realistic user behavior
- **Comprehensive Data Extraction**: 
  - Current price and original price
  - Available offers and promotions
  - Stock status (in stock/out of stock)
  - Product images
  - Page titles
- **Multi-Store Support**: Works with Amazon, Flipkart, Myntra, and other e-commerce sites
- **Error Handling**: Robust error handling with detailed logging
- **JSON Output**: Results saved in structured JSON format

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

## Usage

### Quick Start
```bash
python run_agent.py
```

### Direct Execution
```bash
python agno_agent.py
```

## Output

The agent will create a timestamped JSON file with the following structure:

```json
{
  "scraping_metadata": {
    "total_urls": 27,
    "successful_scrapes": 25,
    "failed_scrapes": 2,
    "scraping_date": "2025-01-09T10:30:00",
    "source_file": "oralb-campaign/Oral B iO3.json"
  },
  "results": [
    {
      "url": "https://www.amazon.in/...",
      "store_name": "amazon.in",
      "scraped_at": "2025-01-09T10:30:15",
      "success": true,
      "error": null,
      "price_info": {
        "current_price": "₹15,955.43",
        "original_price": "₹18,000",
        "discount_percentage": "11%",
        "currency": "₹"
      },
      "offers": [
        "10% off on orders above ₹1000",
        "Free shipping on orders above ₹500"
      ],
      "stock_info": {
        "in_stock": true,
        "stock_status": "In Stock",
        "stock_message": "Usually dispatched within 2-3 days"
      },
      "page_title": "Oral-B iO3 Electric Toothbrush - Amazon.in",
      "product_images": [
        "https://m.media-amazon.com/images/I/..."
      ]
    }
  ]
}
```

## Configuration

### Browser Settings
- **Headless Mode**: Set `headless=True` in the `launch()` method for background operation
- **User Agent**: Realistic Chrome user agent is used by default
- **Timeout**: 30-second timeout for page loads

### Scraping Behavior
- **Delays**: Random delays between 1-3 seconds for human-like behavior
- **Scrolling**: Random scroll patterns to simulate real user interaction
- **Retry Logic**: Built-in error handling for failed requests

## Supported E-commerce Sites

The agent is designed to work with:
- Amazon India
- Flipkart
- Myntra
- Blinkit
- Desert Cart
- Ubuy
- iBhejo
- And other major e-commerce platforms

## Data Extraction

### Price Information
- Current selling price
- Original price (if discounted)
- Currency detection
- Discount percentage calculation

### Offers & Promotions
- Discount codes
- Special offers
- Free shipping
- Limited-time deals
- Bundle offers

### Stock Status
- In stock/Out of stock detection
- Stock availability messages
- Add to cart button status
- Inventory indicators

## Error Handling

The agent includes comprehensive error handling:
- Network timeout handling
- Page load failures
- Element not found errors
- JavaScript execution errors
- Rate limiting protection

## Performance

- **Concurrent Processing**: Sequential processing with delays to avoid rate limiting
- **Memory Efficient**: Proper browser cleanup after each session
- **Progress Tracking**: Real-time progress updates during scraping

## Troubleshooting

### Common Issues

1. **Playwright Installation Issues**:
   ```bash
   playwright install chromium
   ```

2. **Permission Errors**:
   - Run with appropriate permissions
   - Check file write permissions

3. **Network Timeouts**:
   - Increase timeout values in the code
   - Check internet connectivity

4. **Element Not Found**:
   - Sites may have changed their structure
   - Update selectors in the extraction methods

### Debug Mode

To enable debug mode, set `headless=False` in the browser launch configuration to see the browser in action.

## License

This project is for educational and research purposes. Please respect the terms of service of the websites being scraped.

## Contributing

Feel free to contribute by:
- Adding support for new e-commerce sites
- Improving extraction accuracy
- Adding new data fields
- Optimizing performance
