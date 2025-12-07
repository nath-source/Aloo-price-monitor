import requests
from bs4 import BeautifulSoup
import re
import random
import time

def get_product_details(url):
    # List of User-Agents to rotate (makes us look like different browsers)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Add a random delay so we don't hammer the server
        time.sleep(random.uniform(1, 3))
        
        page = requests.get(url, headers=headers, timeout=15)
        
        # Check if they blocked us
        if page.status_code != 200:
            print(f"Blocked! Status Code: {page.status_code}")
            return None, None

        soup = BeautifulSoup(page.content, 'html.parser')
        
        # ... (Keep the rest of your extraction logic exactly the same below) ...
        title = "Unknown Product"
        if soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title")["content"]
        elif soup.find("title"):
            title = soup.find("title").get_text().strip()

        price = 0.0
        
        # Method A: Meta price
        meta_price = soup.find("meta", property="product:price:amount") or \
                     soup.find("meta", property="og:price:amount")
        
        if meta_price:
            try:
                price = float(meta_price["content"])
            except ValueError:
                pass
        
        # Method B: Regex fallback
        if price == 0.0:
            price_text = soup.find(string=re.compile(r"[\$\₵€£]\s?\d+"))
            if price_text:
                clean_price = re.sub(r"[^\d.]", "", price_text)
                try:
                    price = float(clean_price)
                except ValueError:
                    pass

        return title, price

    except Exception as e:
        print(f"Scraping Error: {e}")
        return None, None