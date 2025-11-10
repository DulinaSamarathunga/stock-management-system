# Stock Management System

## Overview
This is a web-based inventory and sales management system built with Flask. It allows users to manage products, track sales, generate invoices, and monitor stock levels through a user-friendly interface. The application includes features for CRUD operations on products, real-time cart management during sales, and responsive design for desktop and mobile use.

## Key Features
- **Product Management**: Add, update, delete, and view products with details like name, category, SKU, price, quantity, and images.
- **Sales Tracking**: Record sales with multi-item support, customer details, payment methods, and automatic inventory updates.
- **Invoice Generation**: View detailed invoices for sales, including itemized products and calculated totals.
- **Low Stock Alerts**: Monitor products with low inventory and receive alerts.
- **Dashboard**: Overview of total products, recent sales, and quick actions.
- **File Uploads**: Secure image uploads for products with previews.
- **API Endpoints**: JSON APIs for product data and stock alerts.
- **Responsive UI**: Mobile-friendly design using Bootstrap and custom CSS.

## Tech Stack
- **Backend**: Python, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript, Bootstrap, Font Awesome, Jinja2 templating
- **Other Libraries**: Werkzeug for file handling

## Project Structure
```
stock-management-system/
│
├── .gitignore                    # Git ignore patterns for Python cache and other files
├── app.py                        # Main Flask application with routes for products, sales, and APIs
├── database.py                   # SQLAlchemy models for Product, Sale, and SaleItem
├── instance/stock.db             # SQLite database file for data storage
├── requirements.txt              # Python dependencies with versions
├── static/style.css              # Custom CSS for dark theme and responsive design
├── templates/
│   ├── base.html                 # Base template with navigation and layout
│   ├── index.html                # Dashboard page with metrics and quick actions
│   ├── products.html             # Product inventory list page
│   ├── add_product.html          # Form for adding new products
│   ├── update_product.html       # Form for updating existing products
│   ├── sales.html                # Sales page with cart management and summary
│   └── invoice.html              # Invoice display page with print functionality
```

## Setup Instructions
1. **Clone the repository** (assuming hosted on a platform like GitHub):
   ```
   git clone <repository-url>
   cd stock-management-system
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up the database**:
   - The application will automatically create tables on first run.
   - Ensure SQLite is available (usually pre-installed on most systems).

4. **Run the application**:
   ```
   python app.py
   ```
   - Access the app at `http://localhost:5000` (default Flask port).

## Usage
- **Dashboard**: View overview metrics, recent sales, and quick action buttons at the root URL (`/`).
- **Products**: Navigate to `/products` to view, add (`/add_product`), update (`/update_product/<id>`), or delete products.
- **Sales**: Go to `/sales` to create bills, manage carts, and record transactions.
- **Invoices**: View specific sale details at `/view_invoice/<sale_id>` with print options.
- **APIs**: Use endpoints like `/api/products` for JSON product data or `/api/low_stock` for alerts.

Upload product images via forms, and use the search and cart features on the sales page for efficient bill creation.

## Contributing
Contributions are welcome. Please fork the repository, create a feature branch, and submit a pull request. Ensure code follows best practices and includes tests if applicable.

## License
This project is licensed under the MIT License. See the LICENSE file for details. (Note: License file not provided in summaries; adjust as needed.)