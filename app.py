from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from database import db, Product, Sale, SaleItem
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from pytz import timezone
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------- DASHBOARD ----------------------
@app.route('/')
def index():
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.quantity < 10).count()
    total_items = db.session.query(db.func.sum(Product.quantity)).scalar() or 0

    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    colombo = timezone("Asia/Colombo")
    for sale in recent_sales:
        sale.local_time = sale.sale_date.astimezone(colombo)

    return render_template('index.html',
                           total_products=total_products,
                           low_stock_products=low_stock_products,
                           total_items=total_items,
                           recent_sales=recent_sales)


# ---------------------- PRODUCTS ----------------------
@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            description = request.form.get('description', '')
            price = float(request.form.get('price', 0) or 0)
            quantity = int(request.form.get('quantity', 0) or 0)
            category = request.form.get('category', '')
            sku = request.form.get('sku', '')
            barcode = request.form.get('barcode', '')

            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_path = filename

            new_product = Product(
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                category=category,
                sku=sku,
                barcode=barcode,
                image_path=image_path
            )

            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')

    return render_template('add_product.html')


@app.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', product.description)
            product.price = float(request.form.get('price', product.price) or product.price)
            product.quantity = int(request.form.get('quantity', product.quantity) or product.quantity)
            product.category = request.form.get('category', product.category)
            product.sku = request.form.get('sku', product.sku)
            product.barcode = request.form.get('barcode', product.barcode)

            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    if product.image_path:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    product.image_path = filename

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')

    return render_template('update_product.html', product=product)


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    try:
        if product.image_path:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')

    return redirect(url_for('products'))


# ---------------------- SALES ----------------------
@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'POST':
        try:
            customer_name = request.form.get('customer_name', 'Walk-in Customer')
            customer_email = request.form.get('customer_email', '')
            customer_phone = request.form.get('customer_phone', '')
            payment_method = request.form.get('payment_method', 'Cash')

            cart_json = request.form.get('cart_data')
            if not cart_json:
                flash('No items in cart!', 'error')
                return redirect(url_for('sales'))

            try:
                cart = json.loads(cart_json)
            except Exception:
                flash('Invalid cart data!', 'error')
                return redirect(url_for('sales'))

            if not isinstance(cart, list) or len(cart) == 0:
                flash('No items in cart!', 'error')
                return redirect(url_for('sales'))

            total_amount = 0.0
            total_discount = 0.0
            cart_items = []

            for entry in cart:
                pid = int(entry.get('product_id'))
                qty = int(entry.get('quantity', 0))
                unit_price = float(entry.get('unit_price', 0) or 0)

                product = Product.query.get(pid)
                if not product:
                    flash(f'Product with id {pid} not found!', 'error')
                    return redirect(url_for('sales'))

                if product.quantity < qty:
                    flash(f'Insufficient stock for {product.name}!', 'error')
                    return redirect(url_for('sales'))

                base_total = unit_price * qty
                discount_value = 0.0

                d_type = entry.get('discountType')
                if d_type == 'percent':
                    pct = float(entry.get('discountPercent', 0) or 0)
                    discount_value = base_total * (pct / 100.0)
                elif d_type == 'fixed':
                    fixed = float(entry.get('discountFixed', 0) or 0)
                    discount_value = min(fixed, base_total)

                item_total_after_discount = base_total - discount_value

                total_amount += base_total
                total_discount += discount_value

                cart_items.append({
                    'product_id': pid,
                    'quantity': qty,
                    'unit_price': unit_price,
                    'base_total': base_total,
                    'discount': discount_value,
                    'total_price': item_total_after_discount,
                    'product': product
                })

            final_amount = total_amount - total_discount

            new_sale = Sale(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                total_amount=total_amount,
                discount_amount=total_discount,
                final_amount=final_amount,
                payment_method=payment_method
            )

            db.session.add(new_sale)
            db.session.flush()

            for item in cart_items:
                sale_item = SaleItem(
                    sale_id=new_sale.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                db.session.add(sale_item)

                prod = Product.query.get(item['product_id'])
                prod.quantity -= item['quantity']

            db.session.commit()
            flash('Sale completed successfully!', 'success')
            return redirect(url_for('view_invoice', sale_id=new_sale.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing sale: {str(e)}', 'error')
            return redirect(url_for('sales'))

    products = Product.query.all()

    all_sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    colombo = timezone("Asia/Colombo")
    for sale in all_sales:
        sale.local_time = sale.sale_date.astimezone(colombo)

    return render_template('sales.html', products=products, sales=all_sales)


# ---------------------- VIEW INVOICE ----------------------
@app.route('/invoice/<int:sale_id>')
def view_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    colombo = timezone("Asia/Colombo")
    sale.local_time = sale.sale_date.astimezone(colombo)

    return render_template('invoice.html', sale=sale)


# ---------------------- DELETE INVOICE (Manager Only) ----------------------
@app.route('/delete_invoice/<int:sale_id>', methods=['GET', 'POST'])
def delete_invoice(sale_id):
    next_url = request.args.get("next")  # <-- get the page to return to

    if request.method == 'POST':
        password = request.form.get('password')

        if password == "Manager123":
            sale = Sale.query.get_or_404(sale_id)

            SaleItem.query.filter_by(sale_id=sale_id).delete()
            db.session.delete(sale)
            db.session.commit()

            flash("Invoice deleted successfully!", "success")

            # Return back safely
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))

        # Incorrect password
        flash("Invalid Manager Password!", "danger")
        return redirect(url_for('delete_invoice', sale_id=sale_id, next=next_url))

    return render_template('confirm_delete.html', sale_id=sale_id, next_url=next_url)

# ---------------------- API ----------------------
@app.route('/api/products')
def api_products():
    products = Product.query.all()
    return jsonify([
        {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': product.quantity,
            'image': product.image_path,
            'sku': product.sku
        } for product in products
    ])


@app.route('/api/low_stock')
def api_low_stock():
    low_stock_products = Product.query.filter(Product.quantity < 10).all()
    return jsonify([
        {
            'id': product.id,
            'name': product.name,
            'quantity': product.quantity,
            'price': product.price
        } for product in low_stock_products
    ])


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ---------------------- DB INIT ----------------------
def create_tables():
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
