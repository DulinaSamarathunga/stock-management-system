from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from database import db, Product, Sale, SaleItem
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Dashboard statistics
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.quantity < 10).count()
    total_items = db.session.query(db.func.sum(Product.quantity)).scalar() or 0
    
    # Recent sales
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         total_items=total_items,
                         recent_sales=recent_sales)

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            category = request.form['category']
            sku = request.form['sku']
            barcode = request.form['barcode']
            
            # Handle file upload
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
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = float(request.form['price'])
            product.quantity = int(request.form['quantity'])
            product.category = request.form['category']
            product.sku = request.form['sku']
            product.barcode = request.form['barcode']
            
            # Handle file upload
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

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'POST':
        try:
            customer_name = request.form.get('customer_name', 'Walk-in Customer')
            customer_email = request.form.get('customer_email', '')
            customer_phone = request.form.get('customer_phone', '')
            payment_method = request.form.get('payment_method', 'Cash')
            
            cart_items = []
            total_amount = 0
            i = 0
            while f'products[{i}][product_id]' in request.form:
                product_id = int(request.form[f'products[{i}][product_id]'])
                quantity = int(request.form[f'products[{i}][quantity]'])
                unit_price = float(request.form[f'products[{i}][unit_price]'])
                
                product = Product.query.get(product_id)
                if product and product.quantity >= quantity:
                    item_total = quantity * unit_price
                    total_amount += item_total
                    
                    cart_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': item_total,
                        'product': product
                    })
                else:
                    flash(f'Insufficient stock for {product.name}!', 'error')
                    return redirect(url_for('sales'))
                
                i += 1
            
            if not cart_items:
                flash('No items in cart!', 'error')
                return redirect(url_for('sales'))
            
            # Calculate final amount (no tax)
            discount_amount = 0
            final_amount = total_amount - discount_amount
            
            # Create sale record
            new_sale = Sale(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                total_amount=total_amount,
                discount_amount=discount_amount,
                final_amount=final_amount,
                payment_method=payment_method
            )
            
            db.session.add(new_sale)
            db.session.flush()  # To get the sale ID
            
            for item in cart_items:
                sale_item = SaleItem(
                    sale_id=new_sale.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                db.session.add(sale_item)
                # Update product quantity
                product = Product.query.get(item['product_id'])
                product.quantity -= item['quantity']
            
            db.session.commit()
            flash('Sale completed successfully!', 'success')
            return redirect(url_for('view_invoice', sale_id=new_sale.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing sale: {str(e)}', 'error')
    
    products = Product.query.all()
    all_sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales.html', products=products, sales=all_sales)

@app.route('/invoice/<int:sale_id>')
def view_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('invoice.html', sale=sale)

@app.route('/api/products')
def api_products():
    products = Product.query.all()
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'quantity': product.quantity,
        'image': product.image_path,
        'sku': product.sku
    } for product in products])

@app.route('/api/low_stock')    
def api_low_stock():
    low_stock_products = Product.query.filter(Product.quantity < 10).all()
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'quantity': product.quantity,
        'price': product.price
    } for product in low_stock_products])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def create_tables():
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
