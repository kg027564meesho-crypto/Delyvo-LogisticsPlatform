import sqlite3
import os
from datetime import datetime
from flask import request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "platform.db")


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def register_admin_module(app):

    # ============================================================
    # ADMIN APP
    # ============================================================

    
    @app.route("/admin/login", methods=["GET"])
    def delyvo_admin_login_alias():
        return render_template("admin_login.html")

    @app.route("/admin")
    def delyvo_admin_login():
        return render_template("admin_login.html")

    
    @app.route("/admin/dashboard", methods=["GET"])
    def delyvo_admin_dashboard_alias():
        return render_template("admin_dashboard.html")

    @app.route("/admin-dashboard")
    def delyvo_admin():
        return render_template("admin_dashboard.html")

    @app.route("/api/admin/login", methods=["POST"])
    def admin_login():
        data = request.get_json(silent=True) or {}

        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not username or not password:
            return jsonify(
                success=False,
                message="Username and password are required"
            ), 400

        import hashlib

        password_hash = hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

        con = db()

        admin = con.execute(
            """
            SELECT admin_id, name, phone, status
            FROM admins
            WHERE name=?
              AND password_hash=?
              AND UPPER(COALESCE(status, ''))='ACTIVE'
            LIMIT 1
            """,
            (username, password_hash)
        ).fetchone()

        con.close()

        if admin:
            return jsonify(
                success=True,
                message="Delyvo Logistics Admin login successful",
                admin={
                    "admin_id": admin["admin_id"],
                    "name": admin["name"],
                    "phone": admin["phone"],
                    "status": admin["status"]
                }
            )

        return jsonify(
            success=False,
            message="Invalid admin credentials"
        ), 401

    # ============================================================
    # ADMIN OVERVIEW
    # ============================================================

    @app.route("/api/admin/dashboard", methods=["GET"])
    def admin_dashboard_api():

        con = db()

        def count(table):
            try:
                return con.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
            except Exception:
                return 0

        stats = {
            "companies": count("companies"),
            "sellers": count("sellers"),
            "products": count("products"),
            "orders": count("orders"),
            "shipments": count("shipments"),
            "hubs": count("hubs"),
            "partners": count("delivery_partners"),
            "payments": count("payments")
        }

        con.close()

        return jsonify(
            success=True,
            platform="Delyvo",
            statistics=stats,
            generated_at=datetime.now().isoformat(timespec="seconds")
        )

    # ============================================================
    # RECENT SHIPMENTS
    # ============================================================

    @app.route("/api/admin/shipments/recent", methods=["GET"])
    def admin_recent_shipments():

        con = db()

        try:
            rows = con.execute("""
                SELECT *
                FROM shipments
                ORDER BY rowid DESC
                LIMIT 20
            """).fetchall()

            shipments = [dict(x) for x in rows]

        except Exception:
            shipments = []

        con.close()

        return jsonify(
            success=True,
            shipments=shipments,
            total=len(shipments)
        )

    # ============================================================
    # HUBS
    # ============================================================

    @app.route("/api/admin/hubs", methods=["GET"])
    def admin_hubs():

        con = db()

        try:
            rows = con.execute("""
                SELECT *
                FROM hubs
                ORDER BY rowid DESC
            """).fetchall()

            hubs = [dict(x) for x in rows]

        except Exception:
            hubs = []

        con.close()

        return jsonify(
            success=True,
            hubs=hubs,
            total=len(hubs)
        )

    # ============================================================
    # PARTNERS
    # ============================================================

    @app.route("/api/admin/partners", methods=["GET"])
    def admin_partners():

        con = db()

        try:
            rows = con.execute("""
                SELECT *
                FROM delivery_partners
                ORDER BY rowid DESC
            """).fetchall()

            partners = [dict(x) for x in rows]

        except Exception:
            partners = []

        con.close()

        return jsonify(
            success=True,
            partners=partners,
            total=len(partners)
        )

    # ============================================================
    # COMPANIES
    # ============================================================

    @app.route("/api/admin/companies", methods=["GET"])
    def admin_companies():

        con = db()

        try:
            rows = con.execute("""
                SELECT
                    company_id,
                    name,
                    email,
                    phone,
                    city,
                    state,
                    pincode,
                    status,
                    created_at
                FROM companies
                ORDER BY id DESC
            """).fetchall()

            companies = [dict(x) for x in rows]

        except Exception:
            companies = []

        con.close()

        return jsonify(
            success=True,
            companies=companies,
            total=len(companies)
        )


    # ============================================================
    # PRODUCTS
    # ============================================================

    @app.route("/api/admin/products", methods=["GET"])
    def admin_products():

        con = db()

        search = str(request.args.get("search", "")).strip()
        seller_id = str(request.args.get("seller_id", "")).strip()
        status = str(request.args.get("status", "")).strip().upper()
        stock_filter = str(request.args.get("stock", "")).strip().lower()

        conditions = []
        params = []

        if search:
            conditions.append("""
                (
                    p.product_id LIKE ?
                    OR p.name LIKE ?
                    OR COALESCE(p.sku, '') LIKE ?
                    OR p.seller_id LIKE ?
                    OR COALESCE(s.name, '') LIKE ?
                    OR COALESCE(s.company_name, '') LIKE ?
                )
            """)
            value = f"%{search}%"
            params.extend([value, value, value, value, value, value])

        if seller_id:
            conditions.append("p.seller_id=?")
            params.append(seller_id)

        if status in {"ACTIVE", "INACTIVE"}:
            conditions.append("p.status=?")
            params.append(status)

        if stock_filter == "low":
            conditions.append("p.stock <= 5")

        elif stock_filter == "out":
            conditions.append("p.stock = 0")

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        try:
            rows = con.execute(f"""
                SELECT
                    p.*,
                    s.name AS seller_name,
                    s.company_name AS seller_company,
                    s.phone AS seller_phone,
                    s.city AS seller_city
                FROM products p
                LEFT JOIN sellers s
                    ON s.seller_id = p.seller_id
                {where}
                ORDER BY p.id DESC
            """, params).fetchall()

            products = [dict(x) for x in rows]

            total = len(products)
            active = sum(
                1 for x in products
                if str(x.get("status", "")).upper() == "ACTIVE"
            )
            inactive = sum(
                1 for x in products
                if str(x.get("status", "")).upper() == "INACTIVE"
            )
            low_stock = sum(
                1 for x in products
                if int(x.get("stock") or 0) <= 5
                and str(x.get("status", "")).upper() == "ACTIVE"
            )
            out_of_stock = sum(
                1 for x in products
                if int(x.get("stock") or 0) == 0
            )

            return jsonify(
                success=True,
                products=products,
                total=total,
                filters={
                    "search": search,
                    "seller_id": seller_id,
                    "status": status,
                    "stock": stock_filter
                },
                summary={
                    "total": total,
                    "active": active,
                    "inactive": inactive,
                    "low_stock": low_stock,
                    "out_of_stock": out_of_stock
                }
            )

        except Exception as e:
            return jsonify(
                success=False,
                message="Unable to load products",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route("/api/admin/products/<product_id>", methods=["GET"])
    def admin_product_detail(product_id):

        con = db()

        try:
            product = con.execute("""
                SELECT
                    p.*,
                    s.name AS seller_name,
                    s.company_name AS seller_company,
                    s.phone AS seller_phone,
                    s.email AS seller_email,
                    s.city AS seller_city,
                    s.status AS seller_status
                FROM products p
                LEFT JOIN sellers s
                    ON s.seller_id = p.seller_id
                WHERE p.product_id=?
            """, (product_id,)).fetchone()

            if not product:
                return jsonify(
                    success=False,
                    message="Product not found"
                ), 404

            return jsonify(
                success=True,
                product=dict(product)
            )

        except Exception as e:
            return jsonify(
                success=False,
                message="Unable to load product",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route(
        "/api/admin/products/<product_id>/stock",
        methods=["POST"]
    )
    def admin_product_stock(product_id):

        data = request.get_json(silent=True) or {}

        try:
            stock = int(data.get("stock"))
        except (TypeError, ValueError):
            return jsonify(
                success=False,
                message="Valid stock is required"
            ), 400

        if stock < 0:
            return jsonify(
                success=False,
                message="Stock cannot be negative"
            ), 400

        con = db()

        try:
            product = con.execute("""
                SELECT product_id
                FROM products
                WHERE product_id=?
            """, (product_id,)).fetchone()

            if not product:
                return jsonify(
                    success=False,
                    message="Product not found"
                ), 404

            updated_at = datetime.now().isoformat(timespec="seconds")

            con.execute("""
                UPDATE products
                SET stock=?,
                    updated_at=?
                WHERE product_id=?
            """, (stock, updated_at, product_id))

            con.commit()

            updated = con.execute("""
                SELECT *
                FROM products
                WHERE product_id=?
            """, (product_id,)).fetchone()

            return jsonify(
                success=True,
                message="Product stock updated successfully",
                product=dict(updated)
            )

        except Exception as e:
            con.rollback()

            return jsonify(
                success=False,
                message="Unable to update product stock",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route(
        "/api/admin/products/<product_id>/status",
        methods=["POST"]
    )
    def admin_product_status(product_id):

        data = request.get_json(silent=True) or {}
        status = str(data.get("status", "")).strip().upper()

        if status not in {"ACTIVE", "INACTIVE"}:
            return jsonify(
                success=False,
                message="Status must be ACTIVE or INACTIVE"
            ), 400

        con = db()

        try:
            product = con.execute("""
                SELECT product_id
                FROM products
                WHERE product_id=?
            """, (product_id,)).fetchone()

            if not product:
                return jsonify(
                    success=False,
                    message="Product not found"
                ), 404

            updated_at = datetime.now().isoformat(timespec="seconds")

            con.execute("""
                UPDATE products
                SET status=?,
                    updated_at=?
                WHERE product_id=?
            """, (status, updated_at, product_id))

            con.commit()

            updated = con.execute("""
                SELECT *
                FROM products
                WHERE product_id=?
            """, (product_id,)).fetchone()

            return jsonify(
                success=True,
                message="Product status updated successfully",
                product=dict(updated)
            )

        except Exception as e:
            con.rollback()

            return jsonify(
                success=False,
                message="Unable to update product status",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route("/api/admin/products/summary", methods=["GET"])
    def admin_product_summary():

        con = db()

        try:
            stats = con.execute("""
                SELECT
                    COUNT(*) AS total_products,
                    COALESCE(
                        SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END),
                        0
                    ) AS active_products,
                    COALESCE(
                        SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END),
                        0
                    ) AS inactive_products,
                    COALESCE(SUM(stock), 0) AS total_stock,
                    COALESCE(
                        SUM(CASE
                            WHEN stock <= 5
                             AND status='ACTIVE'
                            THEN 1 ELSE 0
                        END),
                        0
                    ) AS low_stock_products,
                    COALESCE(
                        SUM(CASE WHEN stock=0 THEN 1 ELSE 0 END),
                        0
                    ) AS out_of_stock_products
                FROM products
            """).fetchone()

            return jsonify(
                success=True,
                summary={
                    "total": int(stats["total_products"] or 0),
                    "active": int(stats["active_products"] or 0),
                    "inactive": int(stats["inactive_products"] or 0),
                    "total_stock": int(stats["total_stock"] or 0),
                    "low_stock": int(stats["low_stock_products"] or 0),
                    "out_of_stock": int(stats["out_of_stock_products"] or 0)
                }
            )

        except Exception as e:
            return jsonify(
                success=False,
                message="Unable to load product summary",
                error=str(e)
            ), 500

        finally:
            con.close()


    # ============================================================
    # ORDERS — ADMIN MANAGEMENT V12
    # ============================================================

    @app.route("/api/admin/orders", methods=["GET"])
    def admin_orders():

        con = db()

        search = str(request.args.get("search", "")).strip()
        seller_id = str(request.args.get("seller_id", "")).strip()
        status = str(request.args.get("status", "")).strip().upper()
        payment_status = str(
            request.args.get("payment_status", "")
        ).strip().upper()

        conditions = []
        params = []

        if search:
            conditions.append("""
                (
                    o.order_id LIKE ?
                    OR o.seller_id LIKE ?
                    OR o.customer_name LIKE ?
                    OR COALESCE(o.customer_phone, '') LIKE ?
                    OR COALESCE(o.shipment_id, '') LIKE ?
                    OR COALESCE(s.name, '') LIKE ?
                    OR COALESCE(s.company_name, '') LIKE ?
                )
            """)

            value = f"%{search}%"

            params.extend([
                value,
                value,
                value,
                value,
                value,
                value,
                value
            ])

        if seller_id:
            conditions.append("o.seller_id=?")
            params.append(seller_id)

        allowed_status = {
            "PLACED",
            "CONFIRMED",
            "PROCESSING",
            "SHIPPED",
            "DELIVERED",
            "CANCELLED"
        }

        if status in allowed_status:
            conditions.append("o.order_status=?")
            params.append(status)

        allowed_payment_status = {
            "PENDING",
            "PAID",
            "FAILED",
            "REFUNDED",
            "COD_COLLECTED"
        }

        if payment_status in allowed_payment_status:
            conditions.append("o.payment_status=?")
            params.append(payment_status)

        where = ""

        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        try:

            rows = con.execute(f"""
                SELECT
                    o.*,

                    s.name AS seller_name,
                    s.phone AS seller_phone,
                    s.email AS seller_email,
                    s.company_name AS seller_company,
                    s.city AS seller_city,

                    (
                        SELECT COUNT(*)
                        FROM order_items oi
                        WHERE oi.order_id=o.order_id
                    ) AS item_count,

                    (
                        SELECT COALESCE(SUM(oi.quantity),0)
                        FROM order_items oi
                        WHERE oi.order_id=o.order_id
                    ) AS total_items

                FROM orders o

                LEFT JOIN sellers s
                    ON s.seller_id=o.seller_id

                {where}

                ORDER BY o.id DESC
            """, params).fetchall()

            orders = [dict(x) for x in rows]

            total_value = sum(
                float(x.get("total_amount") or 0)
                for x in orders
            )

            summary = {
                "total": len(orders),
                "placed": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "PLACED"
                ),
                "confirmed": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "CONFIRMED"
                ),
                "processing": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "PROCESSING"
                ),
                "shipped": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "SHIPPED"
                ),
                "delivered": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "DELIVERED"
                ),
                "cancelled": sum(
                    1 for x in orders
                    if str(x.get("order_status","")).upper()
                    == "CANCELLED"
                ),
                "total_order_value": total_value
            }

            return jsonify(
                success=True,
                orders=orders,
                total=len(orders),
                filters={
                    "search": search,
                    "seller_id": seller_id,
                    "status": status,
                    "payment_status": payment_status
                },
                summary=summary
            )

        except Exception as e:

            return jsonify(
                success=False,
                message="Unable to load orders",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route(
        "/api/admin/orders/<order_id>",
        methods=["GET"]
    )
    def admin_order_detail(order_id):

        con = db()

        try:

            order = con.execute("""
                SELECT
                    o.*,

                    s.name AS seller_name,
                    s.phone AS seller_phone,
                    s.email AS seller_email,
                    s.company_name AS seller_company,
                    s.city AS seller_city,
                    s.status AS seller_status

                FROM orders o

                LEFT JOIN sellers s
                    ON s.seller_id=o.seller_id

                WHERE o.order_id=?
            """, (order_id,)).fetchone()

            if not order:

                return jsonify(
                    success=False,
                    message="Order not found"
                ), 404

            items = con.execute("""
                SELECT *
                FROM order_items
                WHERE order_id=?
                ORDER BY id ASC
            """, (order_id,)).fetchall()

            return jsonify(
                success=True,
                order=dict(order),
                items=[dict(x) for x in items]
            )

        except Exception as e:

            return jsonify(
                success=False,
                message="Unable to load order",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route(
        "/api/admin/orders/<order_id>/status",
        methods=["POST"]
    )
    def admin_order_status(order_id):

        data = request.get_json(silent=True) or {}

        status = str(
            data.get("status", "")
        ).strip().upper()

        allowed = {
            "PLACED",
            "CONFIRMED",
            "PROCESSING",
            "SHIPPED",
            "DELIVERED",
            "CANCELLED"
        }

        if status not in allowed:

            return jsonify(
                success=False,
                message="Invalid order status"
            ), 400

        con = db()

        try:

            order = con.execute("""
                SELECT order_id
                FROM orders
                WHERE order_id=?
            """, (order_id,)).fetchone()

            if not order:

                return jsonify(
                    success=False,
                    message="Order not found"
                ), 404

            updated_at = datetime.now().isoformat(
                timespec="seconds"
            )

            con.execute("""
                UPDATE orders
                SET order_status=?,
                    updated_at=?
                WHERE order_id=?
            """, (
                status,
                updated_at,
                order_id
            ))

            con.commit()

            updated = con.execute("""
                SELECT *
                FROM orders
                WHERE order_id=?
            """, (order_id,)).fetchone()

            return jsonify(
                success=True,
                message="Order status updated successfully",
                order=dict(updated)
            )

        except Exception as e:

            con.rollback()

            return jsonify(
                success=False,
                message="Unable to update order status",
                error=str(e)
            ), 500

        finally:
            con.close()


    @app.route(
        "/api/admin/orders/summary",
        methods=["GET"]
    )
    def admin_order_summary():

        con = db()

        try:

            stats = con.execute("""
                SELECT
                    COUNT(*) AS total_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='PLACED'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS placed_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='CONFIRMED'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS confirmed_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='PROCESSING'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS processing_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='SHIPPED'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS shipped_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='DELIVERED'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS delivered_orders,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN order_status='CANCELLED'
                                THEN 1 ELSE 0
                            END
                        ),0
                    ) AS cancelled_orders,

                    COALESCE(
                        SUM(total_amount),0
                    ) AS total_order_value

                FROM orders
            """).fetchone()

            return jsonify(
                success=True,
                summary={
                    "total": int(
                        stats["total_orders"] or 0
                    ),
                    "placed": int(
                        stats["placed_orders"] or 0
                    ),
                    "confirmed": int(
                        stats["confirmed_orders"] or 0
                    ),
                    "processing": int(
                        stats["processing_orders"] or 0
                    ),
                    "shipped": int(
                        stats["shipped_orders"] or 0
                    ),
                    "delivered": int(
                        stats["delivered_orders"] or 0
                    ),
                    "cancelled": int(
                        stats["cancelled_orders"] or 0
                    ),
                    "total_order_value": float(
                        stats["total_order_value"] or 0
                    )
                }
            )

        except Exception as e:

            return jsonify(
                success=False,
                message="Unable to load order summary",
                error=str(e)
            ), 500

        finally:
            con.close()


    print("Delyvo Admin module registered")
