import sqlite3
from datetime import datetime
from flask import request, jsonify, render_template

DB_PATH = "data/platform.db"


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def register_hub_module(app):

    # ============================================================
    # HUB APP
    # ============================================================

    @app.route("/hub")
    @app.route("/hub-dashboard")
    def delyvo_hub_dashboard():
        return render_template("hub_dashboard.html")

    # ============================================================
    # HUB LIST
    # ============================================================

    @app.route("/api/hub/dashboard", methods=["GET"])
    def hub_dashboard_list():

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
    # HUB DETAIL
    # ============================================================

    @app.route("/api/hub/<hub_code>", methods=["GET"])
    def hub_detail(hub_code):

        con = db()

        try:
            hub = con.execute("""
                SELECT *
                FROM hubs
                WHERE hub_code=?
            """, (hub_code,)).fetchone()
        except Exception:
            hub = None

        if not hub:
            con.close()
            return jsonify(
                success=False,
                message="Hub not found"
            ), 404

        hub_data = dict(hub)

        con.close()

        return jsonify(
            success=True,
            hub=hub_data
        )

    # ============================================================
    # HUB SHIPMENTS
    # ============================================================

    @app.route("/api/hub/<hub_code>/shipments", methods=["GET"])
    def hub_shipments(hub_code):

        con = db()

        try:
            hub = con.execute("""
                SELECT *
                FROM hubs
                WHERE hub_code=?
            """, (hub_code,)).fetchone()

            if not hub:
                con.close()
                return jsonify(
                    success=False,
                    message="Hub not found"
                ), 404

            # Use existing hub shipment assignment API data when
            # the current database schema supports it.
            columns = {
                row["name"]
                for row in con.execute(
                    "PRAGMA table_info(shipments)"
                ).fetchall()
            }

            if "hub_code" not in columns:
                con.close()
                return jsonify(
                    success=True,
                    hub_code=hub_code,
                    shipments=[],
                    total=0,
                    message="Hub shipment linking is ready"
                )

            rows = con.execute("""
                SELECT *
                FROM shipments
                WHERE hub_code=?
                ORDER BY rowid DESC
            """, (hub_code,)).fetchall()

            shipments = [dict(x) for x in rows]

        except Exception as e:
            con.close()
            return jsonify(
                success=False,
                message=str(e)
            ), 500

        con.close()

        return jsonify(
            success=True,
            hub_code=hub_code,
            shipments=shipments,
            total=len(shipments)
        )

    # ============================================================
    # HUB PARTNERS
    # ============================================================

    @app.route("/api/hub/<hub_code>/partners", methods=["GET"])
    def hub_partners(hub_code):

        con = db()

        try:
            rows = con.execute("""
                SELECT *
                FROM delivery_partners
                WHERE hub_code=?
                ORDER BY rowid DESC
            """, (hub_code,)).fetchall()

            partners = [dict(x) for x in rows]

        except Exception:
            partners = []

        con.close()

        return jsonify(
            success=True,
            hub_code=hub_code,
            partners=partners,
            total=len(partners)
        )

    # ============================================================
    # HUB STATUS
    # ============================================================

    @app.route("/api/hub/<hub_code>/status", methods=["POST"])
    def hub_status(hub_code):

        data = request.get_json(silent=True) or {}
        status = str(data.get("status", "")).strip().upper()

        allowed = {
            "ACTIVE",
            "INACTIVE",
            "OPEN",
            "CLOSED"
        }

        if status not in allowed:
            return jsonify(
                success=False,
                message="Invalid hub status",
                allowed_statuses=sorted(allowed)
            ), 400

        con = db()

        try:
            cur = con.execute("""
                UPDATE hubs
                SET status=?
                WHERE hub_code=?
            """, (status, hub_code))

            con.commit()

        except Exception as e:
            con.close()
            return jsonify(
                success=False,
                message=str(e)
            ), 500

        if cur.rowcount == 0:
            con.close()
            return jsonify(
                success=False,
                message="Hub not found"
            ), 404

        con.close()

        return jsonify(
            success=True,
            message="Hub status updated",
            hub_code=hub_code,
            status=status
        )

    print("Delyvo Hub module registered")


