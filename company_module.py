import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from flask import request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "platform.db")


def _db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _rows(con, sql, args=()):
    return [dict(x) for x in con.execute(sql, args).fetchall()]


def _company_id():
    return "COM-" + secrets.token_hex(4).upper()


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_company_routes(app):

    # ============================================================
    # DATABASE MIGRATION
    # ============================================================

    con = _db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_status
        ON companies(status)
    """)

    con.commit()
    con.close()

    # ============================================================
    # COMPANY HOME
    # ============================================================

    @app.route("/company")
    @app.route("/company-dashboard")
    def company_dashboard():
        return render_template("company_dashboard.html")

    # ============================================================
    # CREATE COMPANY
    # ============================================================

    @app.route("/api/companies", methods=["POST"])
    def create_company():
        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        phone = str(data.get("phone", "")).strip()
        address = str(data.get("address", "")).strip()
        city = str(data.get("city", "")).strip()
        state = str(data.get("state", "")).strip()
        pincode = str(data.get("pincode", "")).strip()
        password = str(data.get("password", ""))

        if not name:
            return jsonify(success=False, message="Company name is required"), 400

        if not email:
            return jsonify(success=False, message="Email is required"), 400

        if not password or len(password) < 6:
            return jsonify(
                success=False,
                message="Password must be at least 6 characters"
            ), 400

        con = _db()

        existing = con.execute(
            "SELECT company_id FROM companies WHERE email=?",
            (email,)
        ).fetchone()

        if existing:
            con.close()
            return jsonify(
                success=False,
                message="Company email already exists",
                company_id=existing["company_id"]
            ), 409

        now = datetime.now().isoformat(timespec="seconds")
        company_id = _company_id()

        con.execute("""
            INSERT INTO companies (
                company_id,
                name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                password_hash,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
        """, (
            company_id,
            name,
            email,
            phone,
            address,
            city,
            state,
            pincode,
            _hash_password(password),
            now,
            now
        ))

        con.commit()

        company = dict(con.execute("""
            SELECT
                company_id,
                name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                status,
                created_at,
                updated_at
            FROM companies
            WHERE company_id=?
        """, (company_id,)).fetchone())

        con.close()

        return jsonify(
            success=True,
            message="Company created successfully",
            company=company
        ), 201

    # ============================================================
    # COMPANY LIST
    # ============================================================

    @app.route("/api/companies", methods=["GET"])
    def list_companies():
        con = _db()

        companies = _rows(con, """
            SELECT
                company_id,
                name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                status,
                created_at,
                updated_at
            FROM companies
            ORDER BY id DESC
        """)

        con.close()

        return jsonify(
            success=True,
            companies=companies,
            total=len(companies)
        )

    # ============================================================
    # COMPANY DETAIL
    # ============================================================

    @app.route("/api/companies/<company_id>", methods=["GET"])
    def get_company(company_id):
        con = _db()

        company = con.execute("""
            SELECT
                company_id,
                name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                status,
                created_at,
                updated_at
            FROM companies
            WHERE company_id=?
        """, (company_id,)).fetchone()

        con.close()

        if not company:
            return jsonify(
                success=False,
                message="Company not found"
            ), 404

        return jsonify(
            success=True,
            company=dict(company)
        )

    # ============================================================
    # COMPANY LOGIN
    # ============================================================

    @app.route("/api/companies/login", methods=["POST"])
    def company_login():
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify(
                success=False,
                message="Email and password are required"
            ), 400

        con = _db()

        company = con.execute("""
            SELECT
                company_id,
                name,
                email,
                phone,
                status,
                password_hash
            FROM companies
            WHERE email=?
        """, (email,)).fetchone()

        con.close()

        if not company:
            return jsonify(
                success=False,
                message="Invalid company credentials"
            ), 401

        if company["status"] != "ACTIVE":
            return jsonify(
                success=False,
                message="Company account is not active"
            ), 403

        if _hash_password(password) != company["password_hash"]:
            return jsonify(
                success=False,
                message="Invalid company credentials"
            ), 401

        return jsonify(
            success=True,
            message="Company login successful",
            company={
                "company_id": company["company_id"],
                "name": company["name"],
                "email": company["email"],
                "phone": company["phone"],
                "status": company["status"]
            }
        )

    # ============================================================
    # COMPANY UPDATE
    # ============================================================

    @app.route("/api/companies/<company_id>", methods=["PUT"])
    def update_company(company_id):
        data = request.get_json(silent=True) or {}

        con = _db()

        existing = con.execute(
            "SELECT company_id FROM companies WHERE company_id=?",
            (company_id,)
        ).fetchone()

        if not existing:
            con.close()
            return jsonify(
                success=False,
                message="Company not found"
            ), 404

        fields = []
        values = []

        allowed = [
            "name",
            "phone",
            "address",
            "city",
            "state",
            "pincode"
        ]

        for field in allowed:
            if field in data:
                fields.append(f"{field}=?")
                values.append(str(data[field]).strip())

        if not fields:
            con.close()
            return jsonify(
                success=False,
                message="No fields to update"
            ), 400

        fields.append("updated_at=?")
        values.append(datetime.now().isoformat(timespec="seconds"))
        values.append(company_id)

        con.execute(
            f"""
            UPDATE companies
            SET {", ".join(fields)}
            WHERE company_id=?
            """,
            values
        )

        con.commit()

        company = dict(con.execute("""
            SELECT
                company_id,
                name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                status,
                created_at,
                updated_at
            FROM companies
            WHERE company_id=?
        """, (company_id,)).fetchone())

        con.close()

        return jsonify(
            success=True,
            message="Company updated successfully",
            company=company
        )

    # ============================================================
    # COMPANY STATUS
    # ============================================================

    @app.route("/api/companies/<company_id>/status", methods=["POST"])
    def company_status(company_id):
        data = request.get_json(silent=True) or {}
        status = str(data.get("status", "")).strip().upper()

        allowed = {"ACTIVE", "INACTIVE", "SUSPENDED"}

        if status not in allowed:
            return jsonify(
                success=False,
                message="Invalid company status",
                allowed_statuses=sorted(allowed)
            ), 400

        con = _db()

        cur = con.execute("""
            UPDATE companies
            SET status=?, updated_at=?
            WHERE company_id=?
        """, (
            status,
            datetime.now().isoformat(timespec="seconds"),
            company_id
        ))

        con.commit()

        if cur.rowcount == 0:
            con.close()
            return jsonify(
                success=False,
                message="Company not found"
            ), 404

        con.close()

        return jsonify(
            success=True,
            message="Company status updated",
            company_id=company_id,
            status=status
        )

    # ============================================================
    # COMPANY DASHBOARD
    # ============================================================

    @app.route("/api/companies/<company_id>/dashboard", methods=["GET"])
    def company_dashboard_api(company_id):
        con = _db()

        company = con.execute("""
            SELECT
                company_id,
                name,
                email,
                phone,
                status
            FROM companies
            WHERE company_id=?
        """, (company_id,)).fetchone()

        if not company:
            con.close()
            return jsonify(
                success=False,
                message="Company not found"
            ), 404

        # Shipment tables are already part of the Core platform.
        # This dashboard counts company-linked shipments only when
        # a company_id column exists in the current schema.
        shipment_count = 0
        delivered_count = 0
        pending_count = 0

        columns = {
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(shipments)"
            ).fetchall()
        }

        if "company_id" in columns:
            shipment_count = con.execute(
                "SELECT COUNT(*) FROM shipments WHERE company_id=?",
                (company_id,)
            ).fetchone()[0]

            delivered_count = con.execute("""
                SELECT COUNT(*)
                FROM shipments
                WHERE company_id=?
                AND UPPER(status) IN ('DELIVERED','COMPLETED')
            """, (company_id,)).fetchone()[0]

            pending_count = con.execute("""
                SELECT COUNT(*)
                FROM shipments
                WHERE company_id=?
                AND UPPER(status) NOT IN ('DELIVERED','COMPLETED','CANCELLED')
            """, (company_id,)).fetchone()[0]

        con.close()

        return jsonify(
            success=True,
            company=dict(company),
            statistics={
                "total_shipments": shipment_count,
                "delivered_shipments": delivered_count,
                "pending_shipments": pending_count
            }
        )

    # ============================================================
    # COMPANY SHIPMENTS
    # ============================================================

    @app.route("/api/companies/<company_id>/shipments", methods=["GET"])
    def company_shipments(company_id):
        con = _db()

        company = con.execute(
            "SELECT company_id FROM companies WHERE company_id=?",
            (company_id,)
        ).fetchone()

        if not company:
            con.close()
            return jsonify(
                success=False,
                message="Company not found"
            ), 404

        columns = {
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(shipments)"
            ).fetchall()
        }

        if "company_id" not in columns:
            con.close()
            return jsonify(
                success=True,
                message="Company shipment linking is ready; existing shipments do not yet have company_id",
                shipments=[],
                total=0
            )

        shipments = _rows(con, """
            SELECT *
            FROM shipments
            WHERE company_id=?
            ORDER BY rowid DESC
        """, (company_id,))

        con.close()

        return jsonify(
            success=True,
            company_id=company_id,
            shipments=shipments,
            total=len(shipments)
        )

    print("Delyvo Company module registered")
