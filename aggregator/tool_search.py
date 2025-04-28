import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def search_tools(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search Futurepedia.io for AI tools related to the query.
    
    Args:
        query: The search query
        k: Number of results to return
        
    Returns:
        List of tool dictionaries with name, url, blurb, and tags
    """
    try:
        # Construct the search URL
        search_url = f"https://www.futurepedia.io/search?search={query.replace(' ', '+')}"
        logger.info(f"Searching Futurepedia with URL: {search_url}")
        
        # Send request to Futurepedia
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tool cards based on the new structure
        tool_cards = soup.select('div.bg-card, div.flex.flex-col.bg-card')
        if not tool_cards:
            # Fallback to more generic selectors
            tool_cards = soup.select('div[class*="card"], div[class*="flex flex-col"], a[href*="/tool/"]')
        
        logger.info(f"Found {len(tool_cards)} potential tool cards")
        
        # Limit to k results if k is provided
        if k is not None:
            tool_cards = tool_cards[:k]
        
        results = []
        for card in tool_cards:
            try:
                # Extract tool name - look for the text within a p element with "font-semibold" class
                name_elem = card.select_one('p.font-semibold, p[class*="font-semibold"], h3, h4, a > p')
                name = name_elem.get_text(strip=True) if name_elem else 'Unknown Name'
                
                # Extract tool URL - find a containing href to /tool/
                url_elem = card.select_one('a[href*="/tool/"]')
                url = url_elem['href'] if url_elem and 'href' in url_elem.attrs else '#'
                if not url.startswith('http'):
                    url = f"https://www.futurepedia.io{url}"
                
                # Extract tool description - look for p element with class containing "overflow-hidden"
                blurb_elem = card.select_one('p[class*="overflow-hidden"], p[class*="text-muted"], p[class*="line-clamp"]')
                blurb = blurb_elem.get_text(strip=True) if blurb_elem else 'No description available'
                
                # Extract tags - look for a elements with href containing "/ai-tools/"
                tag_elems = card.select('a[href*="/ai-tools/"]')
                tags = [tag.get_text(strip=True) for tag in tag_elems]
                
                # Also extract pricing info if available
                pricing_elem = card.select_one('div.flex.justify-between span, div.flex span:first-child')
                pricing = pricing_elem.get_text(strip=True) if pricing_elem else ''
                if pricing:
                    tags.append(pricing)
                
                # Extract rating if available
                rating_span = card.select_one('span.sr-only')
                rating = rating_span.get_text(strip=True) if rating_span else ''
                if rating:
                    tags.append(rating)
                
                logger.info(f"Extracted tool: {name}")
                results.append({
                    'name': name,
                    'url': url,
                    'blurb': blurb,
                    'tags': tags
                })
            except Exception as e:
                logger.error(f"Error parsing tool card: {str(e)}")
                continue
                
        logger.info(f"Returning {len(results)} tools")
        return results
        
    except Exception as e:
        logger.error(f"Error searching tools: {str(e)}")
        return [] 