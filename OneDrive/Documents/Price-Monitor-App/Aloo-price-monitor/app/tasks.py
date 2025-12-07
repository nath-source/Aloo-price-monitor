from celery import shared_task
from .extensions import db
from .models import Product
from .scraper import get_product_details
import requests # We use requests instead of smtplib
from datetime import datetime

# --- CONFIGURATION ---
# PASTE YOUR DISCORD WEBHOOK URL INSIDE THE QUOTES BELOW
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1447347739288408176/9FRLzFBT9Nypsu0OvtC7qHOM2DO0aT5C3FccLz8_k5Wx2jjeRfamzfRNh_g9ohyuFGB6"

def send_discord_alert(product_title, price, url):
    print(f"--- Attempting to alert via Discord ---")
    try:
        # Create a fancy card (Embed) for Discord
        payload = {
            "username": "Price Bot",
            "embeds": [{
                "title": "🚨 Price Drop Alert!",
                "description": f"**{product_title}** is now only **${price}**!",
                "color": 5763719, # Green Color
                "url": url,
                "fields": [
                    {"name": "Current Price", "value": f"${price}", "inline": True},
                    {"name": "Link", "value": f"[Buy Now]({url})", "inline": True}
                ]
            }]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print("--- DISCORD ALERT SENT SUCCESS ---")
            return True
        else:
            print(f"--- Discord Failed: {response.status_code} - {response.text} ---")
            return False
            
    except Exception as e:
        print(f"--- Discord Connection Failed: {e} ---")
        return False

@shared_task(ignore_result=False)
def scrape_product_task(product_id):
    print(f"--- Task Started: Scraping Product ID {product_id} ---")
    
    product = Product.query.get(product_id)
    if not product:
        return

    title, price = get_product_details(product.url)

    if title and price:
        product.title = title
        product.current_price = price
        
        # --- LOGIC: ALERT LIMITING ---
        if price <= product.target_price:
            print(f"!!! PRICE ALERT: {title} is ${price} !!!")
            
            # CHECK: Have we sent less than 2 alerts?
            # We re-use the 'email_count' column even though it's now Discord
            if product.email_count < 2:
                # Send to Discord
                sent = send_discord_alert(title, price, product.url)
                if sent:
                    product.email_count += 1
                    product.last_email_sent = datetime.utcnow()
                    print(f"Alert count for this product is now: {product.email_count}")
            else:
                print("--- Alert limit reached (2/2). No alert sent. ---")

        else:
            # PRICE IS HIGH AGAIN
            # Reset the counter so if it drops later, we notify again
            if product.email_count > 0:
                print("Price went back up. Resetting counter to 0.")
                product.email_count = 0
                product.last_email_sent = None
        
        db.session.commit()
        print(f"--- Task Complete: Updated {title} to ${price} ---")
    else:
        print("--- Task Failed: Could not scrape ---")

@shared_task(ignore_result=True)
def update_all_products_task():
    print("--- Scheduled Job: Updating all products ---")
    from app.models import Product
    products = Product.query.all()
    for product in products:
        scrape_product_task.delay(product.id)
    print(f"--- Scheduled Job: Triggered updates for {len(products)} products ---")