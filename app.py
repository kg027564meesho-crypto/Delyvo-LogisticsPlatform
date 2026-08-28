from hub_module import register_hub_module
from admin_module import register_admin_module
from company_module import register_company_routes
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import sqlite3
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "platform.db")

app = Flask(__name__)
CORS(app)


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def now():
    return datetime.now().isoformat(timespec="seconds")


def generate_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def row_to_dict(row):
    return dict(row) if row else None


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            company_name TEXT,
            city TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS hubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hub_id TEXT UNIQUE NOT NULL,
            hub_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id TEXT UNIQUE NOT NULL,
            awb TEXT UNIQUE NOT NULL,
            seller_id TEXT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            pickup_address TEXT,
            delivery_address TEXT NOT NULL,
            origin_hub TEXT,
            current_hub TEXT,
            destination_hub TEXT,
            shipment_type TEXT NOT NULL DEFAULT 'FORWARD',
            status TEXT NOT NULL DEFAULT 'CREATED',
            amount REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS shipment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id TEXT NOT NULL,
            status TEXT NOT NULL,
            hub_code TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)



    db.execute("""
        CREATE TABLE IF NOT EXISTS delivery_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT UNIQUE NOT NULL,
            shipment_id TEXT UNIQUE NOT NULL,
            partner_id TEXT NOT NULL,
            hub_code TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ASSIGNED',
            assigned_at TEXT NOT NULL,
            picked_up_at TEXT,
            completed_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS partner_seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seat_id TEXT UNIQUE NOT NULL,
            hub_code TEXT NOT NULL,
            partner_id TEXT NOT NULL,
            seat_number TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'RESERVED',
            reserved_at TEXT NOT NULL,
            confirmed_at TEXT,
            UNIQUE(hub_code, seat_number)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS delivery_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            city TEXT,
            vehicle_type TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE NOT NULL,
            shipment_id TEXT UNIQUE NOT NULL,
            payment_type TEXT NOT NULL DEFAULT 'COD',
            amount REAL NOT NULL DEFAULT 0,
            collected_amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'PENDING',
            collected_by TEXT,
            collected_at TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS partner_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            earning_id TEXT UNIQUE NOT NULL,
            partner_id TEXT NOT NULL,
            assignment_id TEXT UNIQUE NOT NULL,
            shipment_id TEXT UNIQUE NOT NULL,
            earning_type TEXT NOT NULL DEFAULT 'DELIVERY',
            amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'PENDING',
            payout_id TEXT,
            paid_at TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS bags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bag_id TEXT UNIQUE NOT NULL,
            bag_code TEXT UNIQUE NOT NULL,
            origin_hub TEXT,
            destination_hub TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN',
            seal_code TEXT,
            created_at TEXT NOT NULL,
            sealed_at TEXT,
            dispatched_at TEXT,
            received_at TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS bag_shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bag_id TEXT NOT NULL,
            shipment_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(bag_id, shipment_id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS hub_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movement_id TEXT UNIQUE NOT NULL,
            bag_id TEXT NOT NULL,
            origin_hub TEXT NOT NULL,
            destination_hub TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DISPATCHED',
            dispatched_at TEXT NOT NULL,
            received_at TEXT
        )
    """)


    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            seller_id TEXT NOT NULL,
            name TEXT NOT NULL,
            sku TEXT,
            description TEXT,
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            seller_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            delivery_address TEXT NOT NULL,
            payment_type TEXT NOT NULL DEFAULT 'COD',
            payment_status TEXT NOT NULL DEFAULT 'PENDING',
            order_status TEXT NOT NULL DEFAULT 'PLACED',
            subtotal REAL NOT NULL DEFAULT 0,
            delivery_fee REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL DEFAULT 0,
            shipment_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id TEXT UNIQUE NOT NULL,
            order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            seller_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL DEFAULT 0,
            total_price REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    db.commit()
    db.close()


# =========================================================
# ADMIN MODULE
# =========================================================

@app.route("/api/admins", methods=["POST"])
def create_admin():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "name and phone are required"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT admin_id FROM admins WHERE phone=?",
        (phone,)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Admin with this phone already exists",
            "admin_id": existing["admin_id"]
        }), 409

    admin_id = generate_id("ADM")

    db.execute("""
        INSERT INTO admins
        (admin_id, name, phone, password_hash, status, created_at)
        VALUES (?, ?, ?, ?, 'ACTIVE', ?)
    """, (
        admin_id,
        name,
        phone,
        None,
        now()
    ))

    db.commit()

    admin = db.execute("""
        SELECT id, admin_id, name, phone, status, created_at
        FROM admins
        WHERE admin_id=?
    """, (admin_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Admin created successfully",
        "admin": row_to_dict(admin)
    }), 201


@app.route("/api/admins", methods=["GET"])
def get_admins():
    db = get_db()

    rows = db.execute("""
        SELECT id, admin_id, name, phone, status, created_at
        FROM admins
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "admins": [row_to_dict(x) for x in rows]
    })


@app.route("/api/admins/<admin_id>", methods=["GET"])
def get_admin(admin_id):
    db = get_db()

    admin = db.execute("""
        SELECT id, admin_id, name, phone, status, created_at
        FROM admins
        WHERE admin_id=?
    """, (admin_id,)).fetchone()

    db.close()

    if not admin:
        return jsonify({
            "success": False,
            "message": "Admin not found"
        }), 404

    return jsonify({
        "success": True,
        "admin": row_to_dict(admin)
    })


# =========================================================


# ============================================================
# SELLER PRODUCT API
# ============================================================

@app.route("/api/sellers/<seller_id>/products", methods=["POST"])
def create_seller_product(seller_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    seller = db.execute("""
        SELECT seller_id, status
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    if seller["status"] != "ACTIVE":
        return jsonify({
            "success": False,
            "message": "Seller is inactive"
        }), 400

    name = str(data.get("name", "")).strip()
    sku = str(data.get("sku", "")).strip()
    description = str(data.get("description", "")).strip()

    try:
        price = float(data.get("price", 0))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid price or stock"
        }), 400

    if not name:
        return jsonify({
            "success": False,
            "message": "Product name is required"
        }), 400

    if price < 0 or stock < 0:
        return jsonify({
            "success": False,
            "message": "Price and stock cannot be negative"
        }), 400

    product_id = generate_id("PROD")
    created_at = now()

    db.execute("""
        INSERT INTO products
        (
            product_id,
            seller_id,
            name,
            sku,
            description,
            price,
            stock,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
    """, (
        product_id,
        seller_id,
        name,
        sku,
        description,
        price,
        stock,
        created_at,
        created_at
    ))

    db.commit()

    product = db.execute("""
        SELECT *
        FROM products
        WHERE product_id=?
    """, (product_id,)).fetchone()

    return jsonify({
        "success": True,
        "message": "Product created successfully",
        "product": row_to_dict(product)
    }), 201


@app.route("/api/sellers/<seller_id>/products", methods=["GET"])
def get_seller_products(seller_id):
    db = get_db()
    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    rows = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=?
        ORDER BY id DESC
    """, (seller_id,)).fetchall()

    return jsonify({
        "success": True,
        "seller_id": seller_id,
        "products": [row_to_dict(x) for x in rows],
        "total": len(rows)
    })


@app.route("/api/sellers/<seller_id>/products/<product_id>", methods=["GET"])
def get_seller_product(seller_id, product_id):
    db = get_db()
    product = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if not product:
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    return jsonify({
        "success": True,
        "product": row_to_dict(product)
    })


@app.route("/api/sellers/<seller_id>/products/<product_id>/stock", methods=["POST"])
def update_seller_product_stock(seller_id, product_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    try:
        stock = int(data.get("stock"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Valid stock is required"
        }), 400

    if stock < 0:
        return jsonify({
            "success": False,
            "message": "Stock cannot be negative"
        }), 400

    product = db.execute("""
        SELECT product_id
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if not product:
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    db.execute("""
        UPDATE products
        SET stock=?, updated_at=?
        WHERE seller_id=? AND product_id=?
    """, (
        stock,
        now(),
        seller_id,
        product_id
    ))

    db.commit()

    product = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    return jsonify({
        "success": True,
        "message": "Product stock updated",
        "product": row_to_dict(product)
    })


@app.route("/api/sellers/<seller_id>/products/<product_id>/status", methods=["POST"])
def update_seller_product_status(seller_id, product_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    status = str(data.get("status", "")).strip().upper()

    if status not in {"ACTIVE", "INACTIVE"}:
        return jsonify({
            "success": False,
            "message": "Status must be ACTIVE or INACTIVE"
        }), 400

    product = db.execute("""
        SELECT product_id
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if not product:
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    db.execute("""
        UPDATE products
        SET status=?, updated_at=?
        WHERE seller_id=? AND product_id=?
    """, (
        status,
        now(),
        seller_id,
        product_id
    ))

    db.commit()

    return jsonify({
        "success": True,
        "message": "Product status updated",
        "seller_id": seller_id,
        "product_id": product_id,
        "status": status
    })



# ============================================================
# SELLER ORDER API
# ============================================================

@app.route("/api/sellers/<seller_id>/orders", methods=["POST"])
def create_seller_order(seller_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    seller = db.execute("""
        SELECT seller_id, status
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    if seller["status"] != "ACTIVE":
        return jsonify({
            "success": False,
            "message": "Seller is inactive"
        }), 400

    customer_name = str(data.get("customer_name", "")).strip()
    customer_phone = str(data.get("customer_phone", "")).strip()
    delivery_address = str(data.get("delivery_address", "")).strip()
    payment_type = str(data.get("payment_type", "COD")).strip().upper()

    if not customer_name:
        return jsonify({
            "success": False,
            "message": "Customer name is required"
        }), 400

    if not delivery_address:
        return jsonify({
            "success": False,
            "message": "Delivery address is required"
        }), 400

    if payment_type not in {"COD", "PREPAID"}:
        return jsonify({
            "success": False,
            "message": "Payment type must be COD or PREPAID"
        }), 400

    items = data.get("items", [])

    if not isinstance(items, list) or not items:
        return jsonify({
            "success": False,
            "message": "At least one order item is required"
        }), 400

    prepared_items = []
    subtotal = 0.0

    for item in items:
        product_id = str(item.get("product_id", "")).strip()

        try:
            quantity = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Invalid quantity"
            }), 400

        if not product_id or quantity <= 0:
            return jsonify({
                "success": False,
                "message": "Valid product_id and quantity are required"
            }), 400

        product = db.execute("""
            SELECT *
            FROM products
            WHERE product_id=?
              AND seller_id=?
        """, (product_id, seller_id)).fetchone()

        if not product:
            return jsonify({
                "success": False,
                "message": "Product not found for this seller",
                "product_id": product_id
            }), 404

        if product["status"] != "ACTIVE":
            return jsonify({
                "success": False,
                "message": "Product is inactive",
                "product_id": product_id
            }), 400

        if int(product["stock"]) < quantity:
            return jsonify({
                "success": False,
                "message": "Insufficient product stock",
                "product_id": product_id,
                "available_stock": int(product["stock"])
            }), 400

        unit_price = float(product["price"])
        total_price = unit_price * quantity
        subtotal += total_price

        prepared_items.append({
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price
        })

    try:
        delivery_fee = float(data.get("delivery_fee", 0))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid delivery fee"
        }), 400

    if delivery_fee < 0:
        return jsonify({
            "success": False,
            "message": "Delivery fee cannot be negative"
        }), 400

    total_amount = subtotal + delivery_fee
    order_id = generate_id("ORD")
    created_at = now()

    db.execute("""
        INSERT INTO orders
        (
            order_id,
            seller_id,
            customer_name,
            customer_phone,
            delivery_address,
            payment_type,
            payment_status,
            order_status,
            subtotal,
            delivery_fee,
            total_amount,
            shipment_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        seller_id,
        customer_name,
        customer_phone,
        delivery_address,
        payment_type,
        "PENDING" if payment_type == "COD" else "PAID",
        "PLACED",
        subtotal,
        delivery_fee,
        total_amount,
        None,
        created_at,
        created_at
    ))

    for item in prepared_items:
        order_item_id = generate_id("ITEM")

        db.execute("""
            INSERT INTO order_items
            (
                order_item_id,
                order_id,
                product_id,
                seller_id,
                product_name,
                quantity,
                unit_price,
                total_price,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_item_id,
            order_id,
            item["product_id"],
            seller_id,
            item["product_name"],
            item["quantity"],
            item["unit_price"],
            item["total_price"],
            created_at
        ))

        db.execute("""
            UPDATE products
            SET stock = stock - ?,
                updated_at = ?
            WHERE product_id=?
              AND seller_id=?
        """, (
            item["quantity"],
            created_at,
            item["product_id"],
            seller_id
        ))

    db.commit()

    order = db.execute("""
        SELECT *
        FROM orders
        WHERE order_id=?
    """, (order_id,)).fetchone()

    order_items = db.execute("""
        SELECT *
        FROM order_items
        WHERE order_id=?
        ORDER BY id ASC
    """, (order_id,)).fetchall()

    return jsonify({
        "success": True,
        "message": "Order created successfully",
        "order": row_to_dict(order),
        "items": [row_to_dict(x) for x in order_items]
    }), 201


@app.route("/api/sellers/<seller_id>/orders", methods=["GET"])
def get_seller_orders(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    rows = db.execute("""
        SELECT *
        FROM orders
        WHERE seller_id=?
        ORDER BY id DESC
    """, (seller_id,)).fetchall()

    return jsonify({
        "success": True,
        "seller_id": seller_id,
        "orders": [row_to_dict(x) for x in rows],
        "total": len(rows)
    })


@app.route("/api/sellers/<seller_id>/orders/<order_id>", methods=["GET"])
def get_seller_order(seller_id, order_id):
    db = get_db()

    order = db.execute("""
        SELECT *
        FROM orders
        WHERE seller_id=?
          AND order_id=?
    """, (seller_id, order_id)).fetchone()

    if not order:
        return jsonify({
            "success": False,
            "message": "Order not found"
        }), 404

    items = db.execute("""
        SELECT *
        FROM order_items
        WHERE seller_id=?
          AND order_id=?
        ORDER BY id ASC
    """, (seller_id, order_id)).fetchall()

    return jsonify({
        "success": True,
        "order": row_to_dict(order),
        "items": [row_to_dict(x) for x in items]
    })


@app.route("/api/sellers/<seller_id>/orders/<order_id>/status", methods=["POST"])
def update_seller_order_status(seller_id, order_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    status = str(data.get("status", "")).strip().upper()

    allowed = {
        "PLACED",
        "CONFIRMED",
        "PROCESSING",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED"
    }

    if status not in allowed:
        return jsonify({
            "success": False,
            "message": "Invalid order status"
        }), 400

    order = db.execute("""
        SELECT order_id
        FROM orders
        WHERE seller_id=?
          AND order_id=?
    """, (seller_id, order_id)).fetchone()

    if not order:
        return jsonify({
            "success": False,
            "message": "Order not found"
        }), 404

    db.execute("""
        UPDATE orders
        SET order_status=?,
            updated_at=?
        WHERE seller_id=?
          AND order_id=?
    """, (
        status,
        now(),
        seller_id,
        order_id
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM orders
        WHERE seller_id=?
          AND order_id=?
    """, (seller_id, order_id)).fetchone()

    return jsonify({
        "success": True,
        "message": "Order status updated",
        "order": row_to_dict(updated)
    })


# ============================================================
# SELLER DASHBOARD API
# ============================================================

@app.route("/api/sellers/<seller_id>/dashboard", methods=["GET"])
def get_seller_dashboard(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT seller_id, name, phone, status, created_at
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    product_stats = db.execute("""
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END), 0)
                AS active_products,
            COALESCE(SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END), 0)
                AS inactive_products,
            COALESCE(SUM(stock), 0) AS total_stock
        FROM products
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    order_stats = db.execute("""
        SELECT
            COUNT(*) AS total_orders,
            COALESCE(SUM(CASE WHEN order_status='PLACED' THEN 1 ELSE 0 END), 0)
                AS placed_orders,
            COALESCE(SUM(CASE WHEN order_status='CONFIRMED' THEN 1 ELSE 0 END), 0)
                AS confirmed_orders,
            COALESCE(SUM(CASE WHEN order_status='PROCESSING' THEN 1 ELSE 0 END), 0)
                AS processing_orders,
            COALESCE(SUM(CASE WHEN order_status='SHIPPED' THEN 1 ELSE 0 END), 0)
                AS shipped_orders,
            COALESCE(SUM(CASE WHEN order_status='DELIVERED' THEN 1 ELSE 0 END), 0)
                AS delivered_orders,
            COALESCE(SUM(CASE WHEN order_status='CANCELLED' THEN 1 ELSE 0 END), 0)
                AS cancelled_orders,
            COALESCE(SUM(total_amount), 0) AS total_order_value
        FROM orders
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    recent_orders = db.execute("""
        SELECT
            order_id,
            customer_name,
            customer_phone,
            payment_type,
            payment_status,
            order_status,
            subtotal,
            delivery_fee,
            total_amount,
            created_at,
            updated_at
        FROM orders
        WHERE seller_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (seller_id,)).fetchall()

    low_stock_products = db.execute("""
        SELECT
            product_id,
            name,
            sku,
            price,
            stock,
            status,
            updated_at
        FROM products
        WHERE seller_id=?
          AND status='ACTIVE'
          AND stock <= 5
        ORDER BY stock ASC, id DESC
        LIMIT 10
    """, (seller_id,)).fetchall()

    return jsonify({
        "success": True,
        "seller": row_to_dict(seller),
        "summary": {
            "products": {
                "total": int(product_stats["total_products"] or 0),
                "active": int(product_stats["active_products"] or 0),
                "inactive": int(product_stats["inactive_products"] or 0),
                "total_stock": int(product_stats["total_stock"] or 0)
            },
            "orders": {
                "total": int(order_stats["total_orders"] or 0),
                "placed": int(order_stats["placed_orders"] or 0),
                "confirmed": int(order_stats["confirmed_orders"] or 0),
                "processing": int(order_stats["processing_orders"] or 0),
                "shipped": int(order_stats["shipped_orders"] or 0),
                "delivered": int(order_stats["delivered_orders"] or 0),
                "cancelled": int(order_stats["cancelled_orders"] or 0),
                "total_order_value": float(order_stats["total_order_value"] or 0)
            }
        },
        "recent_orders": [
            row_to_dict(x) for x in recent_orders
        ],
        "low_stock_products": [
            row_to_dict(x) for x in low_stock_products
        ]
    })


@app.route("/api/sellers/<seller_id>/products/summary", methods=["GET"])
def get_seller_product_summary(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    stats = db.execute("""
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END), 0)
                AS active_products,
            COALESCE(SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END), 0)
                AS inactive_products,
            COALESCE(SUM(stock), 0) AS total_stock,
            COALESCE(SUM(CASE WHEN stock <= 5 AND status='ACTIVE'
                              THEN 1 ELSE 0 END), 0)
                AS low_stock_products
        FROM products
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    return jsonify({
        "success": True,
        "seller_id": seller_id,
        "summary": row_to_dict(stats)
    })


@app.route("/api/sellers/<seller_id>/orders/summary", methods=["GET"])
def get_seller_order_summary(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    stats = db.execute("""
        SELECT
            COUNT(*) AS total_orders,
            COALESCE(SUM(CASE WHEN order_status='PLACED'
                              THEN 1 ELSE 0 END), 0) AS placed_orders,
            COALESCE(SUM(CASE WHEN order_status='CONFIRMED'
                              THEN 1 ELSE 0 END), 0) AS confirmed_orders,
            COALESCE(SUM(CASE WHEN order_status='PROCESSING'
                              THEN 1 ELSE 0 END), 0) AS processing_orders,
            COALESCE(SUM(CASE WHEN order_status='SHIPPED'
                              THEN 1 ELSE 0 END), 0) AS shipped_orders,
            COALESCE(SUM(CASE WHEN order_status='DELIVERED'
                              THEN 1 ELSE 0 END), 0) AS delivered_orders,
            COALESCE(SUM(CASE WHEN order_status='CANCELLED'
                              THEN 1 ELSE 0 END), 0) AS cancelled_orders,
            COALESCE(SUM(total_amount), 0) AS total_order_value
        FROM orders
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    return jsonify({
        "success": True,
        "seller_id": seller_id,
        "summary": row_to_dict(stats)
    })


# ============================================================
# SELLER DASHBOARD PAGE
# ============================================================

@app.route("/seller-dashboard/<seller_id>", methods=["GET"])
def seller_dashboard_page(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    return render_template(
        "seller_dashboard.html",
        seller_id=seller_id
    )


# ============================================================
# SELLER PRODUCT MANAGEMENT — EDIT / DELETE
# ============================================================

@app.route("/api/sellers/<seller_id>/products/<product_id>", methods=["PUT"])
def update_seller_product(seller_id, product_id):
    db = get_db()
    data = request.get_json(silent=True) or {}

    product = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if not product:
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    name = str(data.get("name", product["name"])).strip()
    sku = str(data.get("sku", product["sku"] or "")).strip()
    description = str(
        data.get("description", product["description"] or "")
    ).strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Product name is required"
        }), 400

    if not sku:
        return jsonify({
            "success": False,
            "message": "SKU is required"
        }), 400

    try:
        price = float(data.get("price", product["price"]))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid price"
        }), 400

    if price < 0:
        return jsonify({
            "success": False,
            "message": "Price cannot be negative"
        }), 400

    try:
        stock = int(data.get("stock", product["stock"]))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid stock"
        }), 400

    if stock < 0:
        return jsonify({
            "success": False,
            "message": "Stock cannot be negative"
        }), 400

    duplicate = db.execute("""
        SELECT product_id
        FROM products
        WHERE seller_id=?
          AND sku=?
          AND product_id!=?
    """, (seller_id, sku, product_id)).fetchone()

    if duplicate:
        return jsonify({
            "success": False,
            "message": "SKU already exists for this seller"
        }), 409

    updated_at = now()

    db.execute("""
        UPDATE products
        SET name=?,
            sku=?,
            description=?,
            price=?,
            stock=?,
            updated_at=?
        WHERE seller_id=?
          AND product_id=?
    """, (
        name,
        sku,
        description,
        price,
        stock,
        updated_at,
        seller_id,
        product_id
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    return jsonify({
        "success": True,
        "message": "Product updated successfully",
        "product": row_to_dict(updated)
    })


@app.route(
    "/api/sellers/<seller_id>/products/<product_id>",
    methods=["DELETE"]
)
def delete_seller_product(seller_id, product_id):
    db = get_db()

    product = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if not product:
        return jsonify({
            "success": False,
            "message": "Product not found"
        }), 404

    used = db.execute("""
        SELECT COUNT(*) AS total
        FROM order_items
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id)).fetchone()

    if int(used["total"] or 0) > 0:
        return jsonify({
            "success": False,
            "message": "Product cannot be deleted because it is already used in an order"
        }), 409

    db.execute("""
        DELETE FROM products
        WHERE seller_id=? AND product_id=?
    """, (seller_id, product_id))

    db.commit()

    return jsonify({
        "success": True,
        "message": "Product deleted successfully",
        "product_id": product_id
    })


@app.route(
    "/api/sellers/<seller_id>/products/<product_id>/stock",
    methods=["POST"]
)
@app.route(
    "/api/sellers/<seller_id>/products/<product_id>/status",
    methods=["POST"]
)
@app.route("/api/sellers", methods=["POST"])
def create_seller():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    email = str(data.get("email", "")).strip()
    company_name = str(data.get("company_name", "")).strip()
    city = str(data.get("city", "")).strip()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "name and phone are required"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT seller_id FROM sellers WHERE phone=?",
        (phone,)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Seller with this phone already exists",
            "seller_id": existing["seller_id"]
        }), 409

    seller_id = generate_id("SEL")

    db.execute("""
        INSERT INTO sellers
        (seller_id, name, phone, email, company_name, city, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (
        seller_id,
        name,
        phone,
        email,
        company_name,
        city,
        now()
    ))

    db.commit()

    seller = db.execute("""
        SELECT *
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Seller created successfully",
        "seller": row_to_dict(seller)
    }), 201


@app.route("/api/sellers", methods=["GET"])
def get_sellers():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM sellers
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "sellers": [row_to_dict(x) for x in rows]
    })


@app.route("/api/sellers/<seller_id>", methods=["GET"])
def get_seller(seller_id):
    db = get_db()

    seller = db.execute("""
        SELECT *
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    db.close()

    if not seller:
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    return jsonify({
        "success": True,
        "seller": row_to_dict(seller)
    })


@app.route("/api/sellers/<seller_id>/status", methods=["POST"])
def update_seller_status(seller_id):
    data = request.get_json(silent=True) or {}

    status = str(data.get("status", "")).strip().upper()

    if status not in {"ACTIVE", "INACTIVE"}:
        return jsonify({
            "success": False,
            "message": "status must be ACTIVE or INACTIVE"
        }), 400

    db = get_db()

    seller = db.execute("""
        SELECT seller_id
        FROM sellers
        WHERE seller_id=?
    """, (seller_id,)).fetchone()

    if not seller:
        db.close()
        return jsonify({
            "success": False,
            "message": "Seller not found"
        }), 404

    db.execute("""
        UPDATE sellers
        SET status=?
        WHERE seller_id=?
    """, (
        status,
        seller_id
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Seller status updated",
        "seller_id": seller_id,
        "status": status
    })


# =========================================================
# SHIPMENT MODULE
# =========================================================

@app.route("/api/shipments", methods=["POST"])
def create_shipment():
    data = request.get_json(silent=True) or {}

    customer_name = str(data.get("customer_name", "")).strip()
    delivery_address = str(data.get("delivery_address", "")).strip()

    if not customer_name or not delivery_address:
        return jsonify({
            "success": False,
            "message": "customer_name and delivery_address are required"
        }), 400

    seller_id = str(data.get("seller_id", "")).strip()

    db = get_db()

    if seller_id:
        seller = db.execute("""
            SELECT seller_id, status
            FROM sellers
            WHERE seller_id=?
        """, (seller_id,)).fetchone()

        if not seller:
            db.close()
            return jsonify({
                "success": False,
                "message": "Seller not found"
            }), 404

        if seller["status"] != "ACTIVE":
            db.close()
            return jsonify({
                "success": False,
                "message": "Seller is inactive"
            }), 400

    shipment_id = generate_id("SHP")
    awb = generate_id("AWB")
    created = now()

    origin_hub = str(data.get("origin_hub", "")).strip().upper()
    destination_hub = str(data.get("destination_hub", "")).strip().upper()
    shipment_type = str(
        data.get("shipment_type", "FORWARD")
    ).strip().upper()

    try:
        amount = float(data.get("amount", 0) or 0)
    except (TypeError, ValueError):
        db.close()
        return jsonify({
            "success": False,
            "message": "amount must be a valid number"
        }), 400

    db.execute("""
        INSERT INTO shipments (
            shipment_id,
            awb,
            seller_id,
            customer_name,
            customer_phone,
            pickup_address,
            delivery_address,
            origin_hub,
            current_hub,
            destination_hub,
            shipment_type,
            status,
            amount,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        shipment_id,
        awb,
        seller_id or None,
        customer_name,
        str(data.get("customer_phone", "")).strip(),
        str(data.get("pickup_address", "")).strip(),
        delivery_address,
        origin_hub,
        origin_hub,
        destination_hub,
        shipment_type,
        "CREATED",
        amount,
        created,
        created
    ))

    db.execute("""
        INSERT INTO shipment_events (
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        shipment_id,
        "CREATED",
        origin_hub,
        "Shipment created",
        created
    ))

    db.commit()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=?
    """, (shipment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment created successfully",
        "shipment": row_to_dict(shipment)
    }), 201


@app.route("/api/shipments", methods=["GET"])
def get_shipments():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM shipments
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "shipments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/shipments/<shipment_id>", methods=["GET"])
def get_shipment(shipment_id):
    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (
        shipment_id,
        shipment_id
    )).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    events = db.execute("""
        SELECT *
        FROM shipment_events
        WHERE shipment_id=?
        ORDER BY id ASC
    """, (
        shipment["shipment_id"],
    )).fetchall()

    db.close()

    result = row_to_dict(shipment)
    result["events"] = [row_to_dict(x) for x in events]

    return jsonify({
        "success": True,
        "shipment": result
    })

# =========================================================
# HUB MODULE
# =========================================================

@app.route("/api/hubs", methods=["POST"])
def create_hub():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    city = str(data.get("city", "")).strip()
    state = str(data.get("state", "")).strip()
    hub_code = str(data.get("hub_code", "")).strip().upper()

    if not name or not city or not state or not hub_code:
        return jsonify({
            "success": False,
            "message": "name, city, state and hub_code are required"
        }), 400

    db = get_db()

    existing = db.execute(
        "SELECT hub_id FROM hubs WHERE hub_code=?",
        (hub_code,)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub code already exists",
            "hub_id": existing["hub_id"]
        }), 409

    hub_id = generate_id("HUB")

    db.execute("""
        INSERT INTO hubs
        (hub_id, hub_code, name, city, state, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (
        hub_id,
        hub_code,
        name,
        city,
        state,
        now()
    ))

    db.commit()

    hub = db.execute("""
        SELECT *
        FROM hubs
        WHERE hub_id=?
    """, (hub_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Hub created successfully",
        "hub": row_to_dict(hub)
    }), 201


@app.route("/api/hubs", methods=["GET"])
def get_hubs():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM hubs
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "hubs": [row_to_dict(x) for x in rows]
    })


@app.route("/api/hubs/<hub_id>", methods=["GET"])
def get_hub(hub_id):
    db = get_db()

    hub = db.execute("""
        SELECT *
        FROM hubs
        WHERE hub_id=? OR hub_code=?
    """, (
        hub_id,
        hub_id
    )).fetchone()

    db.close()

    if not hub:
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    return jsonify({
        "success": True,
        "hub": row_to_dict(hub)
    })


@app.route("/api/hubs/<hub_id>/status", methods=["POST"])
def update_hub_status(hub_id):
    data = request.get_json(silent=True) or {}

    status = str(data.get("status", "")).strip().upper()

    if status not in {"ACTIVE", "INACTIVE"}:
        return jsonify({
            "success": False,
            "message": "status must be ACTIVE or INACTIVE"
        }), 400

    db = get_db()

    hub = db.execute("""
        SELECT hub_id
        FROM hubs
        WHERE hub_id=? OR hub_code=?
    """, (
        hub_id,
        hub_id
    )).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    db.execute("""
        UPDATE hubs
        SET status=?
        WHERE hub_id=?
    """, (
        status,
        hub["hub_id"]
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Hub status updated",
        "hub_id": hub["hub_id"],
        "status": status
    })

# =========================================================
# BAG & SORTING MODULE
# =========================================================

@app.route("/api/bags", methods=["POST"])
def create_bag():
    data = request.get_json(silent=True) or {}

    origin_hub = str(data.get("origin_hub", "")).strip().upper()
    destination_hub = str(data.get("destination_hub", "")).strip().upper()

    if not origin_hub or not destination_hub:
        return jsonify({
            "success": False,
            "message": "origin_hub and destination_hub are required"
        }), 400

    if origin_hub == destination_hub:
        return jsonify({
            "success": False,
            "message": "Origin and destination hub cannot be same"
        }), 400

    bag_id = generate_id("BAG")
    bag_code = generate_id("BAGCODE")
    created = now()

    db = get_db()

    origin = db.execute("""
        SELECT hub_id
        FROM hubs
        WHERE hub_code=? AND status='ACTIVE'
    """, (origin_hub,)).fetchone()

    destination = db.execute("""
        SELECT hub_id
        FROM hubs
        WHERE hub_code=? AND status='ACTIVE'
    """, (destination_hub,)).fetchone()

    if not origin:
        db.close()
        return jsonify({
            "success": False,
            "message": "Origin hub not found or inactive"
        }), 404

    if not destination:
        db.close()
        return jsonify({
            "success": False,
            "message": "Destination hub not found or inactive"
        }), 404

    db.execute("""
        INSERT INTO bags (
            bag_id,
            bag_code,
            origin_hub,
            destination_hub,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'OPEN', ?)
    """, (
        bag_id,
        bag_code,
        origin_hub,
        destination_hub,
        created
    ))

    db.commit()

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=?
    """, (bag_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Bag created successfully",
        "bag": row_to_dict(bag)
    }), 201


@app.route("/api/bags", methods=["GET"])
def get_bags():
    db = get_db()

    rows = db.execute("""
        SELECT
            b.*,
            COUNT(bs.id) AS shipment_count
        FROM bags b
        LEFT JOIN bag_shipments bs
            ON bs.bag_id=b.bag_id
        GROUP BY b.id
        ORDER BY b.id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "bags": [row_to_dict(x) for x in rows]
    })


@app.route("/api/bags/<bag_id>", methods=["GET"])
def get_bag(bag_id):
    db = get_db()

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=? OR bag_code=?
    """, (
        bag_id,
        bag_id
    )).fetchone()

    if not bag:
        db.close()
        return jsonify({
            "success": False,
            "message": "Bag not found"
        }), 404

    shipments = db.execute("""
        SELECT s.*
        FROM shipments s
        INNER JOIN bag_shipments bs
            ON bs.shipment_id=s.shipment_id
        WHERE bs.bag_id=?
        ORDER BY bs.id ASC
    """, (
        bag["bag_id"],
    )).fetchall()

    db.close()

    result = row_to_dict(bag)
    result["shipment_count"] = len(shipments)
    result["shipments"] = [row_to_dict(x) for x in shipments]

    return jsonify({
        "success": True,
        "bag": result
    })


@app.route("/api/bags/<bag_id>/shipments", methods=["POST"])
def add_shipment_to_bag(bag_id):
    data = request.get_json(silent=True) or {}

    shipment_id = str(data.get("shipment_id", "")).strip()

    if not shipment_id:
        return jsonify({
            "success": False,
            "message": "shipment_id is required"
        }), 400

    db = get_db()

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=? OR bag_code=?
    """, (
        bag_id,
        bag_id
    )).fetchone()

    if not bag:
        db.close()
        return jsonify({
            "success": False,
            "message": "Bag not found"
        }), 404

    if bag["status"] != "OPEN":
        db.close()
        return jsonify({
            "success": False,
            "message": "Only OPEN bags can receive shipments"
        }), 400

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (
        shipment_id,
        shipment_id
    )).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    if shipment["status"] in {"DELIVERED", "CANCELLED", "RETURNED"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment cannot be added to bag in current status"
        }), 400

    if (
        shipment["current_hub"]
        and shipment["current_hub"] != bag["origin_hub"]
    ):
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is not at bag origin hub"
        }), 400

    existing = db.execute("""
        SELECT id
        FROM bag_shipments
        WHERE shipment_id=?
    """, (
        shipment["shipment_id"],
    )).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is already assigned to a bag"
        }), 409

    db.execute("""
        INSERT INTO bag_shipments
        (bag_id, shipment_id, added_at)
        VALUES (?, ?, ?)
    """, (
        bag["bag_id"],
        shipment["shipment_id"],
        now()
    ))

    timestamp = now()

    db.execute("""
        UPDATE shipments
        SET status='AT_ORIGIN_HUB',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        bag["origin_hub"],
        timestamp,
        shipment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'AT_ORIGIN_HUB', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        bag["origin_hub"],
        "Shipment sorted into bag",
        timestamp
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment added to bag successfully",
        "bag_id": bag["bag_id"],
        "shipment_id": shipment["shipment_id"]
    })


@app.route("/api/bags/<bag_id>/seal", methods=["POST"])
def seal_bag(bag_id):
    db = get_db()

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=? OR bag_code=?
    """, (
        bag_id,
        bag_id
    )).fetchone()

    if not bag:
        db.close()
        return jsonify({
            "success": False,
            "message": "Bag not found"
        }), 404

    if bag["status"] != "OPEN":
        db.close()
        return jsonify({
            "success": False,
            "message": "Bag is not OPEN"
        }), 400

    count = db.execute("""
        SELECT COUNT(*)
        FROM bag_shipments
        WHERE bag_id=?
    """, (
        bag["bag_id"],
    )).fetchone()[0]

    if count == 0:
        db.close()
        return jsonify({
            "success": False,
            "message": "Cannot seal an empty bag"
        }), 400

    seal_code = generate_id("SEAL")
    sealed_at = now()

    db.execute("""
        UPDATE bags
        SET status='SEALED',
            seal_code=?,
            sealed_at=?
        WHERE bag_id=?
    """, (
        seal_code,
        sealed_at,
        bag["bag_id"]
    ))

    db.execute("""
        UPDATE shipments
        SET status='IN_TRANSIT',
            updated_at=?
        WHERE shipment_id IN (
            SELECT shipment_id
            FROM bag_shipments
            WHERE bag_id=?
        )
    """, (
        sealed_at,
        bag["bag_id"]
    ))

    shipment_rows = db.execute("""
        SELECT shipment_id
        FROM bag_shipments
        WHERE bag_id=?
    """, (
        bag["bag_id"],
    )).fetchall()

    for row in shipment_rows:
        db.execute("""
            INSERT INTO shipment_events
            (shipment_id, status, hub_code, note, created_at)
            VALUES (?, 'IN_TRANSIT', ?, ?, ?)
        """, (
            row["shipment_id"],
            bag["origin_hub"],
            f"Bag sealed: {seal_code}",
            sealed_at
        ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Bag sealed successfully",
        "bag_id": bag["bag_id"],
        "seal_code": seal_code,
        "shipment_count": count
    })

# =========================================================
# BAG DISPATCH & HUB MOVEMENT MODULE
# =========================================================

@app.route("/api/bags/<bag_id>/dispatch", methods=["POST"])
def dispatch_bag(bag_id):
    db = get_db()

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=? OR bag_code=?
    """, (bag_id, bag_id)).fetchone()

    if not bag:
        db.close()
        return jsonify({
            "success": False,
            "message": "Bag not found"
        }), 404

    if bag["status"] != "SEALED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Only SEALED bags can be dispatched"
        }), 400

    dispatched_at = now()

    db.execute("""
        UPDATE bags
        SET status='DISPATCHED',
            dispatched_at=?
        WHERE bag_id=?
    """, (
        dispatched_at,
        bag["bag_id"]
    ))

    movement_id = generate_id("MOV")

    db.execute("""
        INSERT INTO hub_movements (
            movement_id,
            bag_id,
            origin_hub,
            destination_hub,
            status,
            dispatched_at
        )
        VALUES (?, ?, ?, ?, 'DISPATCHED', ?)
    """, (
        movement_id,
        bag["bag_id"],
        bag["origin_hub"],
        bag["destination_hub"],
        dispatched_at
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Bag dispatched successfully",
        "movement_id": movement_id,
        "bag_id": bag["bag_id"],
        "origin_hub": bag["origin_hub"],
        "destination_hub": bag["destination_hub"],
        "status": "DISPATCHED"
    })


@app.route("/api/movements", methods=["GET"])
def get_movements():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM hub_movements
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "movements": [row_to_dict(x) for x in rows]
    })


@app.route("/api/movements/<movement_id>", methods=["GET"])
def get_movement(movement_id):
    db = get_db()

    movement = db.execute("""
        SELECT *
        FROM hub_movements
        WHERE movement_id=?
    """, (movement_id,)).fetchone()

    if not movement:
        db.close()
        return jsonify({
            "success": False,
            "message": "Movement not found"
        }), 404

    bag = db.execute("""
        SELECT *
        FROM bags
        WHERE bag_id=?
    """, (movement["bag_id"],)).fetchone()

    db.close()

    result = row_to_dict(movement)
    result["bag"] = row_to_dict(bag)

    return jsonify({
        "success": True,
        "movement": result
    })


@app.route("/api/movements/<movement_id>/receive", methods=["POST"])
def receive_movement(movement_id):
    db = get_db()

    movement = db.execute("""
        SELECT *
        FROM hub_movements
        WHERE movement_id=?
    """, (movement_id,)).fetchone()

    if not movement:
        db.close()
        return jsonify({
            "success": False,
            "message": "Movement not found"
        }), 404

    if movement["status"] == "RECEIVED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Movement already received"
        }), 400

    received_at = now()

    db.execute("""
        UPDATE hub_movements
        SET status='RECEIVED',
            received_at=?
        WHERE movement_id=?
    """, (
        received_at,
        movement_id
    ))

    db.execute("""
        UPDATE bags
        SET status='RECEIVED',
            received_at=?
        WHERE bag_id=?
    """, (
        received_at,
        movement["bag_id"]
    ))

    shipment_rows = db.execute("""
        SELECT shipment_id
        FROM bag_shipments
        WHERE bag_id=?
    """, (
        movement["bag_id"],
    )).fetchall()

    for row in shipment_rows:

        db.execute("""
            UPDATE shipments
            SET status='AT_DESTINATION_HUB',
                current_hub=?,
                updated_at=?
            WHERE shipment_id=?
        """, (
            movement["destination_hub"],
            received_at,
            row["shipment_id"]
        ))

        db.execute("""
            INSERT INTO shipment_events (
                shipment_id,
                status,
                hub_code,
                note,
                created_at
            )
            VALUES (?, 'AT_DESTINATION_HUB', ?, ?, ?)
        """, (
            row["shipment_id"],
            movement["destination_hub"],
            "Bag received at destination hub",
            received_at
        ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Bag received successfully",
        "movement_id": movement_id,
        "bag_id": movement["bag_id"],
        "destination_hub": movement["destination_hub"],
        "shipment_count": len(shipment_rows),
        "status": "RECEIVED"
    })

# =========================================================
# DELIVERY & RETURN / RTO MODULE
# =========================================================

@app.route("/api/shipments/<shipment_id>/deliver", methods=["POST"])
def deliver_shipment(shipment_id):
    data = request.get_json(silent=True) or {}

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    if shipment["status"] == "DELIVERED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment already delivered"
        }), 400

    if shipment["status"] in {"CANCELLED", "RETURNED", "RTO"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment cannot be delivered in current status"
        }), 400

    delivered_at = now()
    hub_code = str(
        data.get("hub_code", shipment["current_hub"] or "")
    ).strip().upper()
    note = str(
        data.get("note", "Shipment delivered successfully")
    ).strip()

    db.execute("""
        UPDATE shipments
        SET status='DELIVERED',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        hub_code,
        delivered_at,
        shipment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'DELIVERED', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        hub_code,
        note,
        delivered_at
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment delivered successfully",
        "shipment_id": shipment["shipment_id"],
        "status": "DELIVERED",
        "delivered_at": delivered_at
    })


@app.route("/api/shipments/<shipment_id>/rto", methods=["POST"])
def rto_shipment(shipment_id):
    data = request.get_json(silent=True) or {}

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    if shipment["status"] == "DELIVERED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivered shipment cannot be marked RTO"
        }), 400

    if shipment["status"] in {"RTO", "RETURNED"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is already in return process"
        }), 400

    rto_at = now()
    hub_code = str(
        data.get("hub_code", shipment["current_hub"] or "")
    ).strip().upper()
    reason = str(
        data.get("reason", "Delivery failed")
    ).strip()

    db.execute("""
        UPDATE shipments
        SET status='RTO',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        hub_code,
        rto_at,
        shipment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'RTO', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        hub_code,
        f"RTO initiated: {reason}",
        rto_at
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "RTO initiated successfully",
        "shipment_id": shipment["shipment_id"],
        "status": "RTO",
        "reason": reason
    })


@app.route("/api/shipments/<shipment_id>/return", methods=["POST"])
def return_shipment(shipment_id):
    data = request.get_json(silent=True) or {}

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    if shipment["status"] != "RTO":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment must be in RTO status before return completion"
        }), 400

    returned_at = now()
    hub_code = str(
        data.get("hub_code", shipment["current_hub"] or "")
    ).strip().upper()

    db.execute("""
        UPDATE shipments
        SET status='RETURNED',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        hub_code,
        returned_at,
        shipment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'RETURNED', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        hub_code,
        "Shipment return completed",
        returned_at
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment return completed successfully",
        "shipment_id": shipment["shipment_id"],
        "status": "RETURNED",
        "returned_at": returned_at
    })

# =========================================================
# ADMIN DASHBOARD / PLATFORM SUMMARY MODULE
# =========================================================

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    db = get_db()

    def count(table):
        return db.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

    total_admins = count("admins")
    active_admins = db.execute(
        "SELECT COUNT(*) FROM admins WHERE status='ACTIVE'"
    ).fetchone()[0]

    total_sellers = count("sellers")
    active_sellers = db.execute(
        "SELECT COUNT(*) FROM sellers WHERE status='ACTIVE'"
    ).fetchone()[0]

    total_hubs = count("hubs")
    active_hubs = db.execute(
        "SELECT COUNT(*) FROM hubs WHERE status='ACTIVE'"
    ).fetchone()[0]

    total_shipments = count("shipments")

    shipment_status_rows = db.execute("""
        SELECT status, COUNT(*) AS total
        FROM shipments
        GROUP BY status
        ORDER BY status
    """).fetchall()

    shipment_status = {
        row["status"]: row["total"]
        for row in shipment_status_rows
    }

    total_bags = count("bags")

    bag_status_rows = db.execute("""
        SELECT status, COUNT(*) AS total
        FROM bags
        GROUP BY status
        ORDER BY status
    """).fetchall()

    bag_status = {
        row["status"]: row["total"]
        for row in bag_status_rows
    }

    total_movements = count("hub_movements")

    movement_status_rows = db.execute("""
        SELECT status, COUNT(*) AS total
        FROM hub_movements
        GROUP BY status
        ORDER BY status
    """).fetchall()

    movement_status = {
        row["status"]: row["total"]
        for row in movement_status_rows
    }

    total_value = db.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM shipments
    """).fetchone()[0]

    delivered_value = db.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM shipments
        WHERE status='DELIVERED'
    """).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "dashboard": {
            "admins": {
                "total": total_admins,
                "active": active_admins
            },
            "sellers": {
                "total": total_sellers,
                "active": active_sellers
            },
            "hubs": {
                "total": total_hubs,
                "active": active_hubs
            },
            "shipments": {
                "total": total_shipments,
                "by_status": shipment_status
            },
            "bags": {
                "total": total_bags,
                "by_status": bag_status
            },
            "movements": {
                "total": total_movements,
                "by_status": movement_status
            },
            "financial": {
                "total_shipment_value": total_value,
                "delivered_shipment_value": delivered_value
            }
        }
    })


@app.route("/api/dashboard/recent-shipments", methods=["GET"])
def recent_shipments():
    db = get_db()

    rows = db.execute("""
        SELECT
            shipment_id,
            awb,
            seller_id,
            customer_name,
            delivery_address,
            current_hub,
            destination_hub,
            status,
            amount,
            created_at,
            updated_at
        FROM shipments
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "shipments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/dashboard/recent-movements", methods=["GET"])
def recent_movements():
    db = get_db()

    rows = db.execute("""
        SELECT
            movement_id,
            bag_id,
            origin_hub,
            destination_hub,
            status,
            dispatched_at,
            received_at
        FROM hub_movements
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "movements": [row_to_dict(x) for x in rows]
    })


# =========================================================
# SHIPMENT TRACKING & STATUS MODULE
# =========================================================

@app.route("/api/shipments/<shipment_id>/status", methods=["POST"])
def update_shipment_status(shipment_id):
    data = request.get_json(silent=True) or {}

    new_status = str(data.get("status", "")).strip().upper()
    hub_code = str(data.get("hub_code", "")).strip().upper()
    note = str(data.get("note", "")).strip()

    allowed_statuses = {
        "CREATED",
        "AT_ORIGIN_HUB",
        "IN_TRANSIT",
        "AT_DESTINATION_HUB",
        "OUT_FOR_DELIVERY",
        "DELIVERED",
        "RTO",
        "RETURNED",
        "CANCELLED"
    }

    if new_status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid shipment status",
            "allowed_statuses": sorted(allowed_statuses)
        }), 400

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (
        shipment_id,
        shipment_id
    )).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    current_status = shipment["status"]

    if current_status == "DELIVERED" and new_status != "DELIVERED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivered shipment cannot change status"
        }), 400

    if current_status == "RETURNED" and new_status != "RETURNED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Returned shipment cannot change status"
        }), 400

    updated_at = now()

    if not hub_code:
        hub_code = shipment["current_hub"] or ""

    if not note:
        note = f"Shipment status changed to {new_status}"

    db.execute("""
        UPDATE shipments
        SET status=?,
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        new_status,
        hub_code,
        updated_at,
        shipment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        shipment["shipment_id"],
        new_status,
        hub_code,
        note,
        updated_at
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=?
    """, (
        shipment["shipment_id"],
    )).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment status updated successfully",
        "shipment": row_to_dict(updated)
    })


@app.route("/api/shipments/<shipment_id>/tracking", methods=["GET"])
def shipment_tracking(shipment_id):
    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (
        shipment_id,
        shipment_id
    )).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    events = db.execute("""
        SELECT
            id,
            status,
            hub_code,
            note,
            created_at
        FROM shipment_events
        WHERE shipment_id=?
        ORDER BY id DESC
    """, (
        shipment["shipment_id"],
    )).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "tracking": {
            "shipment_id": shipment["shipment_id"],
            "awb": shipment["awb"],
            "customer_name": shipment["customer_name"],
            "delivery_address": shipment["delivery_address"],
            "origin_hub": shipment["origin_hub"],
            "current_hub": shipment["current_hub"],
            "destination_hub": shipment["destination_hub"],
            "shipment_type": shipment["shipment_type"],
            "status": shipment["status"],
            "amount": shipment["amount"],
            "created_at": shipment["created_at"],
            "updated_at": shipment["updated_at"],
            "events": [row_to_dict(x) for x in events]
        }
    })


@app.route("/api/shipments/<shipment_id>/events", methods=["GET"])
def shipment_events(shipment_id):
    db = get_db()

    shipment = db.execute("""
        SELECT shipment_id
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (
        shipment_id,
        shipment_id
    )).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    rows = db.execute("""
        SELECT
            id,
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        FROM shipment_events
        WHERE shipment_id=?
        ORDER BY id ASC
    """, (
        shipment["shipment_id"],
    )).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "shipment_id": shipment["shipment_id"],
        "events": [row_to_dict(x) for x in rows]
    })


# =========================================================
# COD / PAYMENT MODULE
# =========================================================

@app.route("/api/shipments/<shipment_id>/payment", methods=["POST"])
def create_payment(shipment_id):
    data = request.get_json(silent=True) or {}

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    existing = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (shipment["shipment_id"],)).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Payment already exists for this shipment",
            "payment": row_to_dict(existing)
        }), 409

    payment_type = str(
        data.get("payment_type", "COD")
    ).strip().upper()

    if payment_type not in {"COD", "PREPAID"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "payment_type must be COD or PREPAID"
        }), 400

    try:
        amount = float(
            data.get("amount", shipment["amount"]) or 0
        )
    except (TypeError, ValueError):
        db.close()
        return jsonify({
            "success": False,
            "message": "amount must be a valid number"
        }), 400

    if amount < 0:
        db.close()
        return jsonify({
            "success": False,
            "message": "amount cannot be negative"
        }), 400

    payment_id = generate_id("PAY")
    created_at = now()

    status = "PAID" if payment_type == "PREPAID" else "PENDING"
    collected_amount = amount if payment_type == "PREPAID" else 0
    collected_at = created_at if payment_type == "PREPAID" else None

    db.execute("""
        INSERT INTO payments (
            payment_id,
            shipment_id,
            payment_type,
            amount,
            collected_amount,
            status,
            collected_by,
            collected_at,
            note,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payment_id,
        shipment["shipment_id"],
        payment_type,
        amount,
        collected_amount,
        status,
        "SYSTEM" if payment_type == "PREPAID" else None,
        collected_at,
        "Payment created",
        created_at
    ))

    db.commit()

    payment = db.execute("""
        SELECT *
        FROM payments
        WHERE payment_id=?
    """, (payment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Payment created successfully",
        "payment": row_to_dict(payment)
    }), 201


@app.route("/api/shipments/<shipment_id>/payment", methods=["GET"])
def get_payment(shipment_id):
    db = get_db()

    shipment = db.execute("""
        SELECT shipment_id, awb, customer_name, amount
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    payment = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (shipment["shipment_id"],)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "shipment": row_to_dict(shipment),
        "payment": row_to_dict(payment)
    })


@app.route("/api/shipments/<shipment_id>/payment/collect", methods=["POST"])
def collect_payment(shipment_id):
    data = request.get_json(silent=True) or {}

    db = get_db()

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    payment = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (shipment["shipment_id"],)).fetchone()

    if not payment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Payment record not found"
        }), 404

    if payment["status"] == "PAID":
        db.close()
        return jsonify({
            "success": False,
            "message": "Payment already collected",
            "payment": row_to_dict(payment)
        }), 400

    if payment["payment_type"] != "COD":
        db.close()
        return jsonify({
            "success": False,
            "message": "Only COD payments can be collected"
        }), 400

    try:
        collected_amount = float(
            data.get("collected_amount", payment["amount"]) or 0
        )
    except (TypeError, ValueError):
        db.close()
        return jsonify({
            "success": False,
            "message": "collected_amount must be a valid number"
        }), 400

    if collected_amount != payment["amount"]:
        db.close()
        return jsonify({
            "success": False,
            "message": "Collected amount must match COD amount",
            "required_amount": payment["amount"],
            "received_amount": collected_amount
        }), 400

    collected_by = str(
        data.get("collected_by", "DELIVERY_PARTNER")
    ).strip()

    note = str(
        data.get("note", "COD collected successfully")
    ).strip()

    collected_at = now()

    db.execute("""
        UPDATE payments
        SET collected_amount=?,
            status='PAID',
            collected_by=?,
            collected_at=?,
            note=?
        WHERE payment_id=?
    """, (
        collected_amount,
        collected_by,
        collected_at,
        note,
        payment["payment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events (
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        )
        VALUES (?, 'COD_COLLECTED', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        shipment["current_hub"] or "",
        note,
        collected_at
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM payments
        WHERE payment_id=?
    """, (payment["payment_id"],)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "COD collected successfully",
        "payment": row_to_dict(updated)
    })


@app.route("/api/payments", methods=["GET"])
def get_payments():
    db = get_db()

    rows = db.execute("""
        SELECT
            p.*,
            s.awb,
            s.customer_name,
            s.status AS shipment_status
        FROM payments p
        LEFT JOIN shipments s
            ON s.shipment_id=p.shipment_id
        ORDER BY p.id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "payments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/payments/summary", methods=["GET"])
def payment_summary():
    db = get_db()

    total_payments = db.execute("""
        SELECT COUNT(*)
        FROM payments
    """).fetchone()[0]

    pending_count = db.execute("""
        SELECT COUNT(*)
        FROM payments
        WHERE status='PENDING'
    """).fetchone()[0]

    paid_count = db.execute("""
        SELECT COUNT(*)
        FROM payments
        WHERE status='PAID'
    """).fetchone()[0]

    total_cod = db.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE payment_type='COD'
    """).fetchone()[0]

    collected_cod = db.execute("""
        SELECT COALESCE(SUM(collected_amount), 0)
        FROM payments
        WHERE payment_type='COD'
          AND status='PAID'
    """).fetchone()[0]

    pending_cod = db.execute("""
        SELECT COALESCE(SUM(amount - collected_amount), 0)
        FROM payments
        WHERE payment_type='COD'
          AND status='PENDING'
    """).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "summary": {
            "total_payments": total_payments,
            "pending_payments": pending_count,
            "paid_payments": paid_count,
            "total_cod_amount": total_cod,
            "collected_cod_amount": collected_cod,
            "pending_cod_amount": pending_cod
        }
    })


# =========================================================
# DELIVERY PARTNER MODULE
# =========================================================

@app.route("/api/partners", methods=["POST"])
def create_partner():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    email = str(data.get("email", "")).strip()
    city = str(data.get("city", "")).strip()
    vehicle_type = str(data.get("vehicle_type", "")).strip().upper()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "name and phone are required"
        }), 400

    db = get_db()

    existing = db.execute("""
        SELECT partner_id
        FROM delivery_partners
        WHERE phone=?
    """, (phone,)).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Partner with this phone already exists",
            "partner_id": existing["partner_id"]
        }), 409

    partner_id = generate_id("PTR")
    created_at = now()

    db.execute("""
        INSERT INTO delivery_partners (
            partner_id,
            name,
            phone,
            email,
            city,
            vehicle_type,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (
        partner_id,
        name,
        phone,
        email,
        city,
        vehicle_type,
        created_at
    ))

    db.commit()

    partner = db.execute("""
        SELECT *
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Delivery partner created successfully",
        "partner": row_to_dict(partner)
    }), 201


@app.route("/api/partners", methods=["GET"])
def get_partners():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM delivery_partners
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "partners": [row_to_dict(x) for x in rows]
    })


@app.route("/api/partners/<partner_id>", methods=["GET"])
def get_partner(partner_id):
    db = get_db()

    partner = db.execute("""
        SELECT *
        FROM delivery_partners
        WHERE partner_id=? OR phone=?
    """, (
        partner_id,
        partner_id
    )).fetchone()

    db.close()

    if not partner:
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    return jsonify({
        "success": True,
        "partner": row_to_dict(partner)
    })



# =========================================================
# PARTNER SEAT RESERVATION
# HUB -> PARTNER -> RESERVE -> CONFIRM
# =========================================================

@app.route("/api/hubs/<hub_code>/seats/reserve", methods=["POST"])
def reserve_partner_seat(hub_code):
    data = request.get_json(silent=True) or {}

    partner_id = str(data.get("partner_id", "")).strip()
    seat_number = str(data.get("seat_number", "")).strip()

    if not partner_id or not seat_number:
        return jsonify({
            "success": False,
            "message": "partner_id and seat_number are required"
        }), 400

    db = get_db()

    hub = db.execute("""
        SELECT hub_code
        FROM hubs
        WHERE hub_code=? AND status='ACTIVE'
    """, (hub_code,)).fetchone()

    if not hub:
        return jsonify({
            "success": False,
            "message": "Active hub not found"
        }), 404

    partner = db.execute("""
        SELECT partner_id
        FROM delivery_partners
        WHERE partner_id=? AND status='ACTIVE'
    """, (partner_id,)).fetchone()

    if not partner:
        return jsonify({
            "success": False,
            "message": "Active partner not found"
        }), 404

    existing_partner = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE partner_id=?
          AND status IN ('RESERVED','CONFIRMED')
    """, (partner_id,)).fetchone()

    if existing_partner:
        return jsonify({
            "success": False,
            "message": "Partner already has an active seat reservation",
            "seat": row_to_dict(existing_partner)
        }), 409

    existing_seat = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE hub_code=?
          AND seat_number=?
          AND status IN ('RESERVED','CONFIRMED')
    """, (hub_code, seat_number)).fetchone()

    if existing_seat:
        return jsonify({
            "success": False,
            "message": "This seat is already reserved",
            "seat": row_to_dict(existing_seat)
        }), 409

    seat_id = generate_id("SEAT")
    reserved_at = now()

    db.execute("""
        INSERT INTO partner_seats (
            seat_id,
            hub_code,
            partner_id,
            seat_number,
            status,
            reserved_at
        )
        VALUES (?, ?, ?, ?, 'RESERVED', ?)
    """, (
        seat_id,
        hub_code,
        partner_id,
        seat_number,
        reserved_at
    ))

    db.commit()

    seat = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE seat_id=?
    """, (seat_id,)).fetchone()

    return jsonify({
        "success": True,
        "message": "Seat reserved for partner",
        "seat": row_to_dict(seat)
    }), 201


@app.route("/api/partners/<partner_id>/seat", methods=["GET"])
def partner_reserved_seat(partner_id):

    db = get_db()

    seat = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE partner_id=?
          AND status IN ('RESERVED','CONFIRMED')
        ORDER BY id DESC
        LIMIT 1
    """, (partner_id,)).fetchone()

    return jsonify({
        "success": True,
        "partner_id": partner_id,
        "seat": row_to_dict(seat) if seat else None
    })


@app.route("/api/partner-seats/<seat_id>/confirm", methods=["POST"])
def confirm_partner_seat(seat_id):

    data = request.get_json(silent=True) or {}
    partner_id = str(data.get("partner_id", "")).strip()

    if not partner_id:
        return jsonify({
            "success": False,
            "message": "partner_id is required"
        }), 400

    db = get_db()

    seat = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE seat_id=?
    """, (seat_id,)).fetchone()

    if not seat:
        return jsonify({
            "success": False,
            "message": "Seat reservation not found"
        }), 404

    if seat["partner_id"] != partner_id:
        return jsonify({
            "success": False,
            "message": "This seat belongs to another partner"
        }), 403

    if seat["status"] == "CONFIRMED":
        return jsonify({
            "success": True,
            "message": "Seat already confirmed",
            "seat": row_to_dict(seat)
        })

    if seat["status"] != "RESERVED":
        return jsonify({
            "success": False,
            "message": "Seat is not available for confirmation"
        }), 409

    confirmed_at = now()

    db.execute("""
        UPDATE partner_seats
        SET status='CONFIRMED',
            confirmed_at=?
        WHERE seat_id=?
    """, (
        confirmed_at,
        seat_id
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM partner_seats
        WHERE seat_id=?
    """, (seat_id,)).fetchone()

    return jsonify({
        "success": True,
        "message": "Seat confirmed successfully",
        "seat": row_to_dict(updated)
    })


@app.route("/api/partners/<partner_id>/status", methods=["POST"])
def update_partner_status(partner_id):
    data = request.get_json(silent=True) or {}

    status = str(data.get("status", "")).strip().upper()

    if status not in {"ACTIVE", "INACTIVE"}:
        return jsonify({
            "success": False,
            "message": "status must be ACTIVE or INACTIVE"
        }), 400

    db = get_db()

    partner = db.execute("""
        SELECT partner_id
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    db.execute("""
        UPDATE delivery_partners
        SET status=?
        WHERE partner_id=?
    """, (
        status,
        partner_id
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Partner status updated",
        "partner_id": partner_id,
        "status": status
    })


@app.route("/api/partners/summary", methods=["GET"])
def partner_summary():
    db = get_db()

    total = db.execute("""
        SELECT COUNT(*)
        FROM delivery_partners
    """).fetchone()[0]

    active = db.execute("""
        SELECT COUNT(*)
        FROM delivery_partners
        WHERE status='ACTIVE'
    """).fetchone()[0]

    inactive = db.execute("""
        SELECT COUNT(*)
        FROM delivery_partners
        WHERE status='INACTIVE'
    """).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "summary": {
            "total_partners": total,
            "active_partners": active,
            "inactive_partners": inactive
        }
    })


# =========================================================
# HUB → DELIVERY PARTNER ASSIGNMENT MODULE
# =========================================================

@app.route("/api/hubs/<hub_code>/shipments/available", methods=["GET"])
def hub_available_shipments(hub_code):
    hub_code = str(hub_code).strip().upper()

    db = get_db()

    hub = db.execute("""
        SELECT hub_id, hub_code, name, status
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    if hub["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub is inactive"
        }), 400

    rows = db.execute("""
        SELECT s.*
        FROM shipments s
        WHERE s.current_hub=?
          AND s.status='AT_DESTINATION_HUB'
          AND NOT EXISTS (
              SELECT 1
              FROM delivery_assignments da
              WHERE da.shipment_id=s.shipment_id
                AND da.status IN ('ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY')
          )
        ORDER BY s.id DESC
    """, (hub_code,)).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "hub_code": hub_code,
        "shipments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/hubs/<hub_code>/assign", methods=["POST"])
def assign_shipment_from_hub(hub_code):
    data = request.get_json(silent=True) or {}

    hub_code = str(hub_code).strip().upper()
    shipment_id = str(data.get("shipment_id", "")).strip()
    partner_id = str(data.get("partner_id", "")).strip()

    if not shipment_id or not partner_id:
        return jsonify({
            "success": False,
            "message": "shipment_id and partner_id are required"
        }), 400

    db = get_db()

    hub = db.execute("""
        SELECT *
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    if hub["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub is inactive"
        }), 400

    partner = db.execute("""
        SELECT *
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    if partner["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner is inactive"
        }), 400

    shipment = db.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id=? OR awb=?
    """, (shipment_id, shipment_id)).fetchone()

    if not shipment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment not found"
        }), 404

    if shipment["current_hub"] != hub_code:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is not at this destination hub"
        }), 400

    if shipment["status"] != "AT_DESTINATION_HUB":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is not available for partner assignment"
        }), 400

    existing = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE shipment_id=?
          AND status IN ('ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY')
    """, (shipment["shipment_id"],)).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is already assigned",
            "assignment": row_to_dict(existing)
        }), 409

    assignment_id = generate_id("ASN")
    assigned_at = now()

    db.execute("""
        INSERT INTO delivery_assignments (
            assignment_id,
            shipment_id,
            partner_id,
            hub_code,
            status,
            assigned_at
        )
        VALUES (?, ?, ?, ?, 'ASSIGNED', ?)
    """, (
        assignment_id,
        shipment["shipment_id"],
        partner_id,
        hub_code,
        assigned_at
    ))

    # Partner confirmation is required before shipment becomes OUT_FOR_DELIVERY.
    db.execute("""
        INSERT INTO shipment_events (
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        )
        VALUES (?, 'AT_DESTINATION_HUB', ?, ?, ?)
    """, (
        shipment["shipment_id"],
        hub_code,
        f"Shipment assigned to delivery partner {partner_id}; waiting for partner confirmation",
        assigned_at
    ))

    db.commit()

    assignment = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment assigned from hub successfully",
        "assignment": row_to_dict(assignment)
    }), 201


@app.route("/api/assignments/<assignment_id>/confirm", methods=["POST"])
def confirm_partner_assignment(assignment_id):
    data = request.get_json(silent=True) or {}
    partner_id = str(data.get("partner_id", "")).strip()

    if not partner_id:
        return jsonify({
            "success": False,
            "message": "partner_id is required"
        }), 400

    db = get_db()

    assignment = db.execute("""
        SELECT da.*, s.status AS shipment_status,
               s.current_hub, s.awb
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.assignment_id=?
    """, (assignment_id,)).fetchone()

    if not assignment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment not found"
        }), 404

    if assignment["partner_id"] != partner_id:
        db.close()
        return jsonify({
            "success": False,
            "message": "This shipment is assigned to another partner"
        }), 403

    if assignment["status"] != "ASSIGNED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Only ASSIGNED shipments can be confirmed"
        }), 400

    if assignment["shipment_status"] != "AT_DESTINATION_HUB":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is not waiting for partner confirmation"
        }), 400

    confirmed_at = now()

    # Partner has confirmed the shipment.
    # Assignment becomes PICKED_UP and shipment becomes OUT_FOR_DELIVERY.
    db.execute("""
        UPDATE delivery_assignments
        SET status='PICKED_UP',
            picked_up_at=?
        WHERE assignment_id=?
    """, (
        confirmed_at,
        assignment_id
    ))

    db.execute("""
        UPDATE shipments
        SET status='OUT_FOR_DELIVERY',
            updated_at=?
        WHERE shipment_id=?
    """, (
        confirmed_at,
        assignment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events (
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        )
        VALUES (?, 'OUT_FOR_DELIVERY', ?, ?, ?)
    """, (
        assignment["shipment_id"],
        assignment["hub_code"],
        f"Partner {partner_id} confirmed shipment at hub",
        confirmed_at
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment confirmed by partner and moved OUT_FOR_DELIVERY",
        "assignment": row_to_dict(updated),
        "shipment_id": assignment["shipment_id"],
        "status": "OUT_FOR_DELIVERY",
        "confirmed_at": confirmed_at
    })


@app.route("/api/partners/<partner_id>/assignments", methods=["GET"])
def partner_assignments(partner_id):
    db = get_db()

    partner = db.execute("""
        SELECT *
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    rows = db.execute("""
        SELECT
            da.*,
            s.awb,
            s.customer_name,
            s.customer_phone,
            s.delivery_address,
            s.destination_hub,
            s.status AS shipment_status,
            s.amount
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.partner_id=?
        ORDER BY da.id DESC
    """, (partner_id,)).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "partner_id": partner_id,
        "assignments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/assignments/<assignment_id>/pickup", methods=["POST"])
def pickup_assignment(assignment_id):
    db = get_db()

    assignment = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    if not assignment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment not found"
        }), 404

    if assignment["status"] != "ASSIGNED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Only ASSIGNED shipments can be picked up"
        }), 400

    picked_up_at = now()

    db.execute("""
        UPDATE delivery_assignments
        SET status='PICKED_UP',
            picked_up_at=?
        WHERE assignment_id=?
    """, (
        picked_up_at,
        assignment_id
    ))

    db.execute("""
        INSERT INTO shipment_events (
            shipment_id,
            status,
            hub_code,
            note,
            created_at
        )
        VALUES (?, 'OUT_FOR_DELIVERY', ?, ?, ?)
    """, (
        assignment["shipment_id"],
        assignment["hub_code"],
        "Shipment picked up by delivery partner",
        picked_up_at
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment picked up successfully",
        "assignment_id": assignment_id,
        "status": "PICKED_UP"
    })

# =========================================================
# STEP 14 — PARTNER DELIVERY / RTO CONTROL
# =========================================================

@app.route("/api/assignments/<assignment_id>/deliver", methods=["POST"])
def complete_partner_delivery(assignment_id):
    data = request.get_json(silent=True) or {}

    partner_id = str(data.get("partner_id", "")).strip()
    note = str(data.get("note", "Shipment delivered successfully")).strip()
    hub_code = str(data.get("hub_code", "")).strip().upper()

    if not partner_id:
        return jsonify({
            "success": False,
            "message": "partner_id is required"
        }), 400

    db = get_db()

    assignment = db.execute("""
        SELECT da.*, s.status AS shipment_status,
               s.current_hub, s.awb
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.assignment_id=?
    """, (assignment_id,)).fetchone()

    if not assignment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment not found"
        }), 404

    # HUB-ONLY CONTROL:
    # Delivery partner can act only on an assignment created by a hub.
    if not assignment["hub_code"]:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment has no valid hub assignment"
        }), 403

    if assignment["partner_id"] != partner_id:
        db.close()
        return jsonify({
            "success": False,
            "message": "This shipment is assigned to another partner"
        }), 403

    if assignment["status"] not in {"ASSIGNED", "PICKED_UP", "OUT_FOR_DELIVERY"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment cannot be completed in current status"
        }), 400

    if assignment["shipment_status"] == "DELIVERED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment already delivered"
        }), 400

    if assignment["shipment_status"] in {"RTO", "RETURNED", "CANCELLED"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment cannot be delivered in current status"
        }), 400

    payment = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (assignment["shipment_id"],)).fetchone()

    if payment and payment["payment_type"] == "COD":
        if payment["status"] != "PAID":
            db.close()
            return jsonify({
                "success": False,
                "message": "COD payment must be collected before delivery",
                "payment_status": payment["status"],
                "required_amount": payment["amount"]
            }), 400

    delivered_at = now()

    if not hub_code:
        hub_code = assignment["hub_code"] or assignment["current_hub"] or ""

    db.execute("""
        UPDATE shipments
        SET status='DELIVERED',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        hub_code,
        delivered_at,
        assignment["shipment_id"]
    ))

    db.execute("""
        UPDATE delivery_assignments
        SET status='COMPLETED',
            completed_at=?
        WHERE assignment_id=?
    """, (
        delivered_at,
        assignment_id
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'DELIVERED', ?, ?, ?)
    """, (
        assignment["shipment_id"],
        hub_code,
        note,
        delivered_at
    ))

    # PARTNER EARNING
    # One earning record per completed assignment.
    existing_earning = db.execute("""
        SELECT earning_id
        FROM partner_earnings
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    if not existing_earning:
        earning_id = generate_id("ERN")

        db.execute("""
            INSERT INTO partner_earnings (
                earning_id,
                partner_id,
                assignment_id,
                shipment_id,
                earning_type,
                amount,
                status,
                payout_id,
                paid_at,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, 'DELIVERY', ?, 'PENDING', NULL, NULL, ?, ?)
        """, (
            earning_id,
            partner_id,
            assignment_id,
            assignment["shipment_id"],
            50.0,
            "Delivery earning created automatically",
            delivered_at
        ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment delivered successfully",
        "assignment": row_to_dict(updated),
        "shipment_id": assignment["shipment_id"],
        "status": "DELIVERED",
        "delivered_at": delivered_at
    })


@app.route("/api/assignments/<assignment_id>/rto", methods=["POST"])
def partner_rto(assignment_id):
    data = request.get_json(silent=True) or {}

    partner_id = str(data.get("partner_id", "")).strip()
    reason = str(data.get("reason", "Delivery failed")).strip()
    hub_code = str(data.get("hub_code", "")).strip().upper()

    if not partner_id:
        return jsonify({
            "success": False,
            "message": "partner_id is required"
        }), 400

    db = get_db()

    assignment = db.execute("""
        SELECT da.*, s.status AS shipment_status,
               s.current_hub, s.awb
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.assignment_id=?
    """, (assignment_id,)).fetchone()

    if not assignment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment not found"
        }), 404

    # HUB-ONLY CONTROL:
    # Delivery partner can act only on an assignment created by a hub.
    if not assignment["hub_code"]:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment has no valid hub assignment"
        }), 403

    if assignment["partner_id"] != partner_id:
        db.close()
        return jsonify({
            "success": False,
            "message": "This shipment is assigned to another partner"
        }), 403

    if assignment["status"] not in {"ASSIGNED", "PICKED_UP", "OUT_FOR_DELIVERY"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment cannot be marked RTO in current status"
        }), 400

    if assignment["shipment_status"] == "DELIVERED":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivered shipment cannot be marked RTO"
        }), 400

    if assignment["shipment_status"] in {"RTO", "RETURNED", "CANCELLED"}:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is already in return/cancelled state"
        }), 400

    rto_at = now()

    if not hub_code:
        hub_code = assignment["hub_code"] or assignment["current_hub"] or ""

    db.execute("""
        UPDATE shipments
        SET status='RTO',
            current_hub=?,
            updated_at=?
        WHERE shipment_id=?
    """, (
        hub_code,
        rto_at,
        assignment["shipment_id"]
    ))

    db.execute("""
        UPDATE delivery_assignments
        SET status='RTO',
            completed_at=?
        WHERE assignment_id=?
    """, (
        rto_at,
        assignment_id
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'RTO', ?, ?, ?)
    """, (
        assignment["shipment_id"],
        hub_code,
        f"RTO initiated by delivery partner {partner_id}: {reason}",
        rto_at
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM delivery_assignments
        WHERE assignment_id=?
    """, (assignment_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Shipment marked RTO successfully",
        "assignment": row_to_dict(updated),
        "shipment_id": assignment["shipment_id"],
        "status": "RTO",
        "reason": reason,
        "rto_at": rto_at
    })


@app.route("/api/partners/<partner_id>/active-assignments", methods=["GET"])
def partner_active_assignments(partner_id):
    db = get_db()

    partner = db.execute("""
        SELECT partner_id, name, phone, status
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    if partner["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner is inactive"
        }), 400

    rows = db.execute("""
        SELECT
            da.*,
            s.awb,
            s.customer_name,
            s.customer_phone,
            s.delivery_address,
            s.current_hub,
            s.destination_hub,
            s.status AS shipment_status,
            s.amount
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.partner_id=?
          AND da.status IN ('ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY')
        ORDER BY da.id DESC
    """, (partner_id,)).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "partner_id": partner_id,
        "assignments": [row_to_dict(x) for x in rows]
    })

# =========================================================
# STEP 16 — HUB ASSIGNMENT MANAGEMENT
# =========================================================

@app.route("/api/hubs/<hub_code>/assignments", methods=["GET"])
def hub_assignments(hub_code):
    hub_code = str(hub_code).strip().upper()
    db = get_db()

    hub = db.execute("""
        SELECT hub_id, hub_code, name, status
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    rows = db.execute("""
        SELECT
            da.*,
            s.awb,
            s.customer_name,
            s.customer_phone,
            s.delivery_address,
            s.destination_hub,
            s.status AS shipment_status,
            s.amount,
            p.name AS partner_name,
            p.phone AS partner_phone
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        LEFT JOIN delivery_partners p
            ON p.partner_id=da.partner_id
        WHERE da.hub_code=?
        ORDER BY da.id DESC
    """, (hub_code,)).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "hub_code": hub_code,
        "assignments": [row_to_dict(x) for x in rows]
    })


@app.route("/api/hubs/<hub_code>/assignments/summary", methods=["GET"])
def hub_assignment_summary(hub_code):
    hub_code = str(hub_code).strip().upper()
    db = get_db()

    hub = db.execute("""
        SELECT hub_id, hub_code, name, status
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    total = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
    """, (hub_code,)).fetchone()[0]

    assigned = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=? AND status='ASSIGNED'
    """, (hub_code,)).fetchone()[0]

    picked_up = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=? AND status='PICKED_UP'
    """, (hub_code,)).fetchone()[0]

    completed = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=? AND status='COMPLETED'
    """, (hub_code,)).fetchone()[0]

    rto = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=? AND status='RTO'
    """, (hub_code,)).fetchone()[0]

    active = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
          AND status IN ('ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY')
    """, (hub_code,)).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "hub_code": hub_code,
        "summary": {
            "total_assignments": total,
            "assigned": assigned,
            "picked_up": picked_up,
            "active": active,
            "completed": completed,
            "rto": rto
        }
    })

# =========================================================
# STEP 17 — PARTNER COD COLLECTION CONTROL
# =========================================================

@app.route("/api/assignments/<assignment_id>/collect-cod", methods=["POST"])
def partner_collect_cod(assignment_id):
    data = request.get_json(silent=True) or {}

    partner_id = str(data.get("partner_id", "")).strip()
    note = str(data.get("note", "COD collected by delivery partner")).strip()

    if not partner_id:
        return jsonify({
            "success": False,
            "message": "partner_id is required"
        }), 400

    db = get_db()

    assignment = db.execute("""
        SELECT da.*, s.status AS shipment_status
        FROM delivery_assignments da
        INNER JOIN shipments s
            ON s.shipment_id=da.shipment_id
        WHERE da.assignment_id=?
    """, (assignment_id,)).fetchone()

    if not assignment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Assignment not found"
        }), 404

    if not assignment["hub_code"]:
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment has no valid hub assignment"
        }), 403

    if assignment["partner_id"] != partner_id:
        db.close()
        return jsonify({
            "success": False,
            "message": "This shipment is assigned to another partner"
        }), 403

    if assignment["status"] not in {
        "ASSIGNED",
        "PICKED_UP",
        "OUT_FOR_DELIVERY"
    }:
        db.close()
        return jsonify({
            "success": False,
            "message": "COD cannot be collected in current assignment status"
        }), 400

    if assignment["shipment_status"] in {
        "DELIVERED",
        "RTO",
        "RETURNED",
        "CANCELLED"
    }:
        db.close()
        return jsonify({
            "success": False,
            "message": "COD cannot be collected for this shipment"
        }), 400

    payment = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (assignment["shipment_id"],)).fetchone()

    if not payment:
        db.close()
        return jsonify({
            "success": False,
            "message": "Payment record not found"
        }), 404

    if payment["payment_type"] != "COD":
        db.close()
        return jsonify({
            "success": False,
            "message": "Shipment is not COD"
        }), 400

    if payment["status"] == "PAID":
        db.close()
        return jsonify({
            "success": False,
            "message": "COD payment already collected",
            "payment": row_to_dict(payment)
        }), 409

    amount = float(payment["amount"] or 0)
    collected_at = now()

    db.execute("""
        UPDATE payments
        SET collected_amount=?,
            status='PAID',
            collected_by=?,
            collected_at=?,
            note=?
        WHERE shipment_id=?
    """, (
        amount,
        partner_id,
        collected_at,
        note,
        assignment["shipment_id"]
    ))

    db.execute("""
        INSERT INTO shipment_events
        (shipment_id, status, hub_code, note, created_at)
        VALUES (?, 'OUT_FOR_DELIVERY', ?, ?, ?)
    """, (
        assignment["shipment_id"],
        assignment["hub_code"],
        f"COD collected by delivery partner {partner_id}",
        collected_at
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM payments
        WHERE shipment_id=?
    """, (assignment["shipment_id"],)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "COD collected successfully",
        "assignment_id": assignment_id,
        "partner_id": partner_id,
        "shipment_id": assignment["shipment_id"],
        "payment": row_to_dict(updated)
    })

# =========================================================
# STEP 21 — HUB DASHBOARD
# =========================================================

@app.route("/api/hubs/<hub_code>/dashboard", methods=["GET"])
def hub_dashboard(hub_code):
    hub_code = str(hub_code).strip().upper()
    db = get_db()

    hub = db.execute("""
        SELECT hub_id, hub_code, name, city, state, status
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    total_shipments = db.execute("""
        SELECT COUNT(*)
        FROM shipments
        WHERE current_hub=?
    """, (hub_code,)).fetchone()[0]

    available_shipments = db.execute("""
        SELECT COUNT(*)
        FROM shipments s
        WHERE s.current_hub=?
          AND s.status='AT_DESTINATION_HUB'
          AND NOT EXISTS (
              SELECT 1
              FROM delivery_assignments da
              WHERE da.shipment_id=s.shipment_id
                AND da.status IN (
                    'ASSIGNED',
                    'PICKED_UP',
                    'OUT_FOR_DELIVERY'
                )
          )
    """, (hub_code,)).fetchone()[0]

    total_assignments = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
    """, (hub_code,)).fetchone()[0]

    active_assignments = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
          AND status IN (
              'ASSIGNED',
              'PICKED_UP',
              'OUT_FOR_DELIVERY'
          )
    """, (hub_code,)).fetchone()[0]

    completed_assignments = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
          AND status='COMPLETED'
    """, (hub_code,)).fetchone()[0]

    rto_assignments = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE hub_code=?
          AND status='RTO'
    """, (hub_code,)).fetchone()[0]

    partners_total = db.execute("""
        SELECT COUNT(*)
        FROM delivery_partners
        WHERE status='ACTIVE'
    """).fetchone()[0]

    payments_pending = db.execute("""
        SELECT COUNT(*)
        FROM payments p
        INNER JOIN shipments s
            ON s.shipment_id=p.shipment_id
        WHERE s.current_hub=?
          AND p.status='PENDING'
          AND p.payment_type='COD'
    """, (hub_code,)).fetchone()[0]

    cod_pending_amount = db.execute("""
        SELECT COALESCE(SUM(p.amount - p.collected_amount), 0)
        FROM payments p
        INNER JOIN shipments s
            ON s.shipment_id=p.shipment_id
        WHERE s.current_hub=?
          AND p.status='PENDING'
          AND p.payment_type='COD'
    """, (hub_code,)).fetchone()[0]

    db.close()

    return jsonify({
        "success": True,
        "hub": row_to_dict(hub),
        "dashboard": {
            "shipments": {
                "total": total_shipments,
                "available_for_assignment": available_shipments
            },
            "assignments": {
                "total": total_assignments,
                "active": active_assignments,
                "completed": completed_assignments,
                "rto": rto_assignments
            },
            "partners": {
                "active_total": partners_total
            },
            "cod": {
                "pending_payments": payments_pending,
                "pending_amount": cod_pending_amount
            }
        }
    })

# =========================================================
# STEP 23 — HUB ACTIVE PARTNERS
# =========================================================

@app.route("/api/hubs/<hub_code>/partners", methods=["GET"])
def hub_active_partners(hub_code):
    hub_code = str(hub_code).strip().upper()
    db = get_db()

    hub = db.execute("""
        SELECT hub_id, hub_code, name, city, state, status
        FROM hubs
        WHERE hub_code=?
    """, (hub_code,)).fetchone()

    if not hub:
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub not found"
        }), 404

    if hub["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Hub is inactive"
        }), 400

    rows = db.execute("""
        SELECT
            partner_id,
            name,
            phone,
            email,
            city,
            vehicle_type,
            status,
            created_at
        FROM delivery_partners
        WHERE status='ACTIVE'
        ORDER BY name ASC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "hub_code": hub_code,
        "partners": [row_to_dict(x) for x in rows]
    })

# =========================================================
# STEP 38 — PARTNER DASHBOARD
# =========================================================


@app.route("/api/partners/<partner_id>/earnings", methods=["GET"])
def partner_earnings(partner_id):
    db = get_db()

    partner = db.execute("""
        SELECT *
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Partner not found"
        }), 404

    rows = db.execute("""
        SELECT *
        FROM partner_earnings
        WHERE partner_id=?
        ORDER BY id DESC
    """, (partner_id,)).fetchall()

    summary = db.execute("""
        SELECT
            COUNT(*) AS total_earnings,
            COALESCE(SUM(amount), 0) AS total_amount,
            COALESCE(SUM(CASE WHEN status='PENDING' THEN amount ELSE 0 END), 0) AS pending_amount,
            COALESCE(SUM(CASE WHEN status='PAID' THEN amount ELSE 0 END), 0) AS paid_amount
        FROM partner_earnings
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "partner_id": partner_id,
        "summary": dict(summary),
        "earnings": [dict(row) for row in rows]
    })



@app.route("/api/partners/<partner_id>/earnings/<earning_id>/payout", methods=["POST"])
def partner_earning_payout(partner_id, earning_id):
    partner_id = str(partner_id).strip()
    earning_id = str(earning_id).strip()

    db = get_db()

    earning = db.execute("""
        SELECT *
        FROM partner_earnings
        WHERE partner_id=? AND earning_id=?
    """, (partner_id, earning_id)).fetchone()

    if not earning:
        db.close()
        return jsonify({
            "success": False,
            "message": "Earning not found"
        }), 404

    if earning["status"] == "PAID":
        db.close()
        return jsonify({
            "success": False,
            "message": "Earning already paid",
            "earning": dict(earning)
        }), 409

    payout_id = generate_id("PAY")

    paid_at = now()

    db.execute("""
        UPDATE partner_earnings
        SET status='PAID',
            payout_id=?,
            paid_at=?,
            note=?
        WHERE earning_id=? AND partner_id=? AND status='PENDING'
    """, (
        payout_id,
        paid_at,
        "Partner earning payout completed",
        earning_id,
        partner_id
    ))

    db.commit()

    updated = db.execute("""
        SELECT *
        FROM partner_earnings
        WHERE partner_id=? AND earning_id=?
    """, (partner_id, earning_id)).fetchone()

    db.close()

    return jsonify({
        "success": True,
        "message": "Partner earning paid successfully",
        "payout_id": payout_id,
        "earning": dict(updated)
    })


@app.route("/admin-partners", methods=["GET"])
def admin_partners_dashboard():
    return render_template("admin_partners.html")

@app.route("/partner-dashboard", methods=["GET"])
def partner_dashboard_page():
    return render_template("partner_dashboard.html")

@app.route("/api/partners/<partner_id>/dashboard", methods=["GET"])
def partner_dashboard(partner_id):
    partner_id = str(partner_id).strip()
    db = get_db()

    partner = db.execute("""
        SELECT partner_id, name, phone, email, city,
               vehicle_type, status, created_at
        FROM delivery_partners
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    if not partner:
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner not found"
        }), 404

    if partner["status"] != "ACTIVE":
        db.close()
        return jsonify({
            "success": False,
            "message": "Delivery partner is inactive"
        }), 400

    active = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE partner_id=?
          AND status IN (
              'ASSIGNED',
              'PICKED_UP',
              'OUT_FOR_DELIVERY'
          )
    """, (partner_id,)).fetchone()[0]

    completed = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE partner_id=?
          AND status='COMPLETED'
    """, (partner_id,)).fetchone()[0]

    rto = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE partner_id=?
          AND status='RTO'
    """, (partner_id,)).fetchone()[0]

    total_assignments = db.execute("""
        SELECT COUNT(*)
        FROM delivery_assignments
        WHERE partner_id=?
    """, (partner_id,)).fetchone()[0]

    cod_collected = db.execute("""
        SELECT
            COUNT(*) AS payments,
            COALESCE(SUM(p.collected_amount), 0) AS amount
        FROM payments p
        INNER JOIN delivery_assignments da
            ON da.shipment_id=p.shipment_id
        WHERE da.partner_id=?
          AND p.payment_type='COD'
          AND p.status='PAID'
          AND p.collected_by=?
    """, (partner_id, partner_id)).fetchone()

    cod_pending = db.execute("""
        SELECT
            COUNT(*) AS payments,
            COALESCE(SUM(
                CASE
                    WHEN p.amount > p.collected_amount
                    THEN p.amount - p.collected_amount
                    ELSE 0
                END
            ), 0) AS amount
        FROM payments p
        INNER JOIN delivery_assignments da
            ON da.shipment_id=p.shipment_id
        WHERE da.partner_id=?
          AND p.payment_type='COD'
          AND p.status='PENDING'
    """, (partner_id,)).fetchone()


    earning_summary = db.execute("""
        SELECT
            COUNT(*) AS total_earnings,
            COALESCE(SUM(amount), 0) AS total_amount,
            COALESCE(SUM(
                CASE WHEN status='PENDING'
                THEN amount ELSE 0 END
            ), 0) AS pending_amount,
            COALESCE(SUM(
                CASE WHEN status='PAID'
                THEN amount ELSE 0 END
            ), 0) AS paid_amount
        FROM partner_earnings
        WHERE partner_id=?
    """, (partner_id,)).fetchone()

    recent_earnings = db.execute("""
        SELECT
            earning_id,
            assignment_id,
            shipment_id,
            earning_type,
            amount,
            status,
            payout_id,
            paid_at,
            note,
            created_at
        FROM partner_earnings
        WHERE partner_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (partner_id,)).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "partner": row_to_dict(partner),
        "dashboard": {
            "assignments": {
                "total": total_assignments,
                "active": active,
                "completed": completed,
                "rto": rto
            },
            "cod": {
                "collected_payments": cod_collected["payments"],
                "collected_amount": cod_collected["amount"],
                "pending_payments": cod_pending["payments"],
                "pending_amount": cod_pending["amount"]
            },
            "earnings": {
                "total_earnings": earning_summary["total_earnings"],
                "total_amount": earning_summary["total_amount"],
                "pending_amount": earning_summary["pending_amount"],
                "paid_amount": earning_summary["paid_amount"],
                "recent": [dict(row) for row in recent_earnings]
            }
        }
    })


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "platform": "Core Logistics Platform",
        "version": "1.0",
        "status": "ONLINE"
    })


@app.route("/api/health")
def health():
    db = get_db()

    db.execute("SELECT 1").fetchone()

    db.close()

    return jsonify({
        "success": True,
        "status": "ONLINE",
        "database": "CONNECTED"
    })



# Register Delyvo Company module
register_company_routes(app)

# Register Delyvo Admin module
register_admin_module(app)

# Register Delyvo Hub module
register_hub_module(app)

if __name__ == "__main__":
    init_db()

    print("=" * 40)
    print(" CORE LOGISTICS PLATFORM")
    print(" Backend v1.0")
    print("=" * 40)
    print(f"Database: {DB_PATH}")
    print("Server: http://127.0.0.1:5001")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )

# ============================================================
# DELYVO MARKET CUSTOMER APP
# ============================================================

@app.route("/market")
@app.route("/delyvo-market")
def delyvo_market():
    return app.send_static_file("market-placeholder.html") if False else render_template("delyvo_market.html")
