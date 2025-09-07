#!/usr/bin/env python3
"""
Script to map data from Flipkart and Amazon JSON files into the main Oral B iO3.json file
based on URL source (Flipkart vs Amazon).
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return {}

def is_flipkart_url(url: str) -> bool:
    """Check if URL is from Flipkart."""
    return 'flipkart.com' in url.lower()

def is_amazon_url(url: str) -> bool:
    """Check if URL is from Amazon."""
    return 'amazon.in' in url.lower() or 'amazon.com' in url.lower()

def find_matching_offer_in_source(source_data: Dict[str, Any], target_url: str) -> Optional[Dict[str, Any]]:
    """Find matching offer in source data by URL."""
    if not source_data or 'variants' not in source_data:
        return None
    
    for variant in source_data['variants']:
        if 'store_links' not in variant:
            continue
        
        for offer in variant['store_links']:
            if offer.get('url') == target_url:
                return offer
    
    return None

def merge_offer_data(target_offer: Dict[str, Any], source_offer: Dict[str, Any]) -> Dict[str, Any]:
    """Merge additional data from source offer into target offer."""
    # Fields to potentially merge from source
    additional_fields = [
        'in_stock',
        'platform_url', 
        'product_name_via_url',
        'ranked_offers'
    ]
    
    merged_offer = target_offer.copy()
    
    for field in additional_fields:
        if field in source_offer and field not in merged_offer:
            merged_offer[field] = source_offer[field]
        elif field in source_offer and field in merged_offer:
            # If both have the field, prefer the source (newer) data
            merged_offer[field] = source_offer[field]
    
    return merged_offer

def map_oralb_data():
    """Main function to map data from Flipkart and Amazon files into main JSON."""
    
    # File paths
    main_file = "Oral B iO3.json"
    flipkart_file = "Oral_B_iO3_flipkart_offers_20250905_002202.json"
    amazon_file = "Oral_B_iO3_amazon_20250905_001420.json"
    
    print("Loading JSON files...")
    
    # Load all JSON files
    main_data = load_json_file(main_file)
    flipkart_data = load_json_file(flipkart_file)
    amazon_data = load_json_file(amazon_file)
    
    if not main_data:
        print("Error: Could not load main data file")
        return
    
    print(f"Loaded main data with {len(main_data.get('variants', []))} variants")
    print(f"Loaded Flipkart data with {len(flipkart_data.get('variants', []))} variants")
    print(f"Loaded Amazon data with {len(amazon_data.get('variants', []))} variants")
    
    # Statistics
    stats = {
        'flipkart_matches': 0,
        'amazon_matches': 0,
        'no_matches': 0,
        'total_offers_processed': 0
    }
    
    # Process each variant in main data
    for variant_idx, variant in enumerate(main_data.get('variants', [])):
        print(f"\nProcessing variant {variant_idx + 1}: {variant.get('color', 'Unknown')} - {variant.get('packaging_type', 'Unknown')}")
        
        if 'store_links' not in variant:
            continue
        
        # Process each offer in the variant
        for offer_idx, offer in enumerate(variant['store_links']):
            stats['total_offers_processed'] += 1
            url = offer.get('url', '')
            
            if not url:
                continue
            
            source_offer = None
            source_name = None
            
            # Check if it's a Flipkart URL
            if is_flipkart_url(url):
                source_offer = find_matching_offer_in_source(flipkart_data, url)
                source_name = "Flipkart"
                if source_offer:
                    stats['flipkart_matches'] += 1
                    print(f"  ✓ Found Flipkart match for: {url[:60]}...")
            
            # Check if it's an Amazon URL
            elif is_amazon_url(url):
                source_offer = find_matching_offer_in_source(amazon_data, url)
                source_name = "Amazon"
                if source_offer:
                    stats['amazon_matches'] += 1
                    print(f"  ✓ Found Amazon match for: {url[:60]}...")
            
            # If no match found
            if not source_offer:
                stats['no_matches'] += 1
                print(f"  ✗ No match found for: {url[:60]}...")
                continue
            
            # Merge the data
            merged_offer = merge_offer_data(offer, source_offer)
            variant['store_links'][offer_idx] = merged_offer
            
            # Print what was merged
            merged_fields = []
            for field in ['in_stock', 'platform_url', 'product_name_via_url', 'ranked_offers']:
                if field in source_offer and field not in offer:
                    merged_fields.append(field)
            
            if merged_fields:
                print(f"    Merged fields: {', '.join(merged_fields)}")
    
    # Update metadata
    if 'metadata' not in main_data:
        main_data['metadata'] = {}
    
    main_data['metadata']['mapping_timestamp'] = datetime.now().isoformat()
    main_data['metadata']['mapping_stats'] = stats
    
    # Save the updated data
    output_file = f"Oral_B_iO3_mapped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully saved mapped data to: {output_file}")
        
        # Print summary statistics
        print(f"\n📊 Mapping Summary:")
        print(f"  Total offers processed: {stats['total_offers_processed']}")
        print(f"  Flipkart matches: {stats['flipkart_matches']}")
        print(f"  Amazon matches: {stats['amazon_matches']}")
        print(f"  No matches: {stats['no_matches']}")
        print(f"  Success rate: {((stats['flipkart_matches'] + stats['amazon_matches']) / stats['total_offers_processed'] * 100):.1f}%")
        
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    map_oralb_data()

