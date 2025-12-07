import requests
from bs4 import BeautifulSoup
import re
import random
import time

def get_product_details(url):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    ]

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        # REMOVED "Accept-Encoding" - Let requests handle this automatically
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Random delay to look human
        time.sleep(random.uniform(1, 3))
        
        page = requests.get(url, headers=headers, timeout=15)
        
        # Debug Log for Render
        print(f"--- Scraper Status Code: {page.status_code} ---")
        
        if page.status_code != 200:
            return None, None

        soup = BeautifulSoup(page.content, 'html.parser')
        
        # 1. Extract Title
        title = "Unknown Product"
        if soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title")["content"]
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        elif soup.find("title"):
            title = soup.find("title").get_text().strip()

        # 2. Extract Price
        price = 0.0
        
        # Method A: Meta Tags
        meta_price = soup.find("meta", property="product:price:amount") or \
                     soup.find("meta", property="og:price:amount")
        
        if meta_price:
            try:
                price = float(meta_price["content"])
            except ValueError:
                pass
        
        # Method B: Visual Scrape (Look for currency symbols)
        if price == 0.0:
            # Look for elements containing $ or £
            price_candidates = soup.find_all(string=re.compile(r"[\$\£\€]\s?\d+"))
            for candidate in price_candidates:
                text = candidate.strip()
                # Clean up the string (remove non-numeric chars except dot)
                clean_price = re.sub(r"[^\d.]", "", text)
                try:
                    found_price = float(clean_price)
                    if found_price > 0:
                        price = found_price
                        break # Stop at the first valid price
                except ValueError:
                    continue

        return title, price

    except Exception as e:
        print(f"Scraping Error: {e}")
        return None, None