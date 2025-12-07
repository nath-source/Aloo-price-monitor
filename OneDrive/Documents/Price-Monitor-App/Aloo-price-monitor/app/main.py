from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .extensions import db
from .models import Product
from .tasks import scrape_product_task # <--- Import the task

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        url = request.form.get('url')
        target_price = request.form.get('target_price')

        if not url or not target_price:
            flash("Please fill in all fields.")
            return redirect(url_for('main.dashboard'))

        # 1. SAVE TO DB IMMEDIATELY (Placeholder data)
        new_product = Product(
            title="Fetching details...", 
            url=url,
            target_price=float(target_price),
            current_price=None,
            user_id=current_user.id
        )
        
        db.session.add(new_product)
        db.session.commit()

        # 2. TRIGGER ASYNC TASK
        # This sends the ID to Redis. The worker picks it up.
        scrape_product_task.delay(new_product.id)
        
        flash("Tracking started! We are checking the price in the background.")
        return redirect(url_for('main.dashboard'))

    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', products=products)

@main.route('/delete/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id == current_user.id:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted.')
    return redirect(url_for('main.dashboard'))