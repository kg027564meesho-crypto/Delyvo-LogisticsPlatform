import sqlite3
from datetime import datetime
from flask import request, jsonify, render_template

DB_PATH = "data/platform.db"


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def register_admin_module(app):

    # ============================================================
    # ADMIN APP
    # ============================================================

    @app.route("/admin")
    @app.route("/admin-dashboard")
    def delyvo_admin():
        return render_template("admin_dashboard.html")

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

    print("Delyvo Admin module registered")
