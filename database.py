from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone

db = SQLAlchemy()

# Sri Lanka timezone
colombo = timezone("Asia/Colombo")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))
    sku = db.Column(db.String(50), unique=True)
    barcode = db.Column(db.String(100))
    image_path = db.Column(db.String(200))

    # Correct Sri Lanka time for created_at
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(colombo)
    )

    sale_items = db.relationship(
        'SaleItem',
        backref='product',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Product {self.name}>'


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='Cash')

    # Correct Sri Lanka time for sale_date
    sale_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(colombo)
    )

    sale_items = db.relationship(
        'SaleItem',
        backref='sale',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Sale {self.id}>'


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<SaleItem {self.product_id} {self.quantity}>'
