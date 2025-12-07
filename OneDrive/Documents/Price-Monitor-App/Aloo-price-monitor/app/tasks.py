from celery import shared_task
from .extensions import db
from .models import Product, User
from .scraper import get_product_details
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SENDER_EMAIL = "nathanielademola499@gmail.com"  # <--- Put your email back here
APP_PASSWORD = "hcsw nduo ofbf kooa"     # <--- Put your password back here

def send_email_alert(product_title, price, url, user_email):
    print(f"--- Attempting to email {user_email} ---")
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = f"Price Drop Alert: {product_title}!"

        body = f"""
        <html>
          <body>
            <h2>Good news!</h2>
            <p>The price for <strong>{product_title}</strong> has dropped to <strong>${price}</strong>.</p>
            <p><a href="{url}">Click here to buy it now</a></p>
          </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"--- EMAIL SENT SUCCESS to {user_email} ---")
        return True
    except Exception as e:
        print(f"--- Email Failed Error: {e} ---")
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
        
        # --- LOGIC: EMAIL LIMITING ---
        if price <= product.target_price:
            print(f"!!! PRICE ALERT: {title} is ${price} !!!")
            
            # CHECK: Have we sent less than 2 emails?
            if product.email_count < 2:
                user = User.query.get(product.user_id)
                if user and user.email:
                    # Send the email
                    sent = send_email_alert(title, price, product.url, user.email)
                    if sent:
                        product.email_count += 1
                        product.last_email_sent = datetime.utcnow()
                        print(f"Email count for this product is now: {product.email_count}")
            else:
                print("--- Email limit reached (2/2). No email sent. ---")

        else:
            # PRICE IS HIGH AGAIN
            # Reset the counter so if it drops later, we notify again
            if product.email_count > 0:
                print("Price went back up. Resetting email counter to 0.")
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