#!/usr/bin/env python3
"""
Test script to verify that the modified Flipkart scraper can correctly extract
Flipkart URLs from the Oral B iO3.json structure
"""

import json
import sys
import os

# Add the current directory to the path so we can import the scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_flipkart_scraper_comprehensive import ComprehensiveFlipkartExtractor

def test_flipkart_extraction():
    """Test the Flipkart URL extraction from Oral B iO3.json"""
    
    # Load the JSON data
    input_file = "Oral B iO3.json"
    
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        return False
    
    print(f"📖 Loading data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded JSON data successfully")
    print(f"📱 Product: {data.get('toothbrush_name', 'Unknown')}")
    print(f"📊 Total variants: {len(data.get('variants', []))}")
    
    # Initialize the extractor
    extractor = ComprehensiveFlipkartExtractor(input_file)
    
    # Find Flipkart links
    print(f"\n🔍 Searching for Flipkart links...")
    flipkart_links = extractor.find_all_flipkart_store_links(data)
    
    print(f"\n📊 RESULTS:")
    print(f"   Total Flipkart links found: {len(flipkart_links)}")
    
    if flipkart_links:
        print(f"\n🔗 Flipkart URLs found:")
        for i, link in enumerate(flipkart_links, 1):
            print(f"   {i}. {link['name']}")
            print(f"      URL: {link['url']}")
            print(f"      Price: {link['price']}")
            print(f"      Path: {link['path']}")
            print()
    else:
        print(f"   ❌ No Flipkart links found!")
        return False
    
    # Test output filename generation
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_flipkart_offers_{timestamp}.json"
    
    print(f"📝 Generated output filename: {output_file}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Flipkart URL extraction from Oral B iO3.json")
    print("=" * 60)
    
    success = test_flipkart_extraction()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("   The modified scraper can correctly extract Flipkart URLs")
        print("   from the Oral B iO3.json structure.")
    else:
        print("\n❌ Test failed!")
        print("   There was an issue with the URL extraction.")
    
    print("=" * 60)


