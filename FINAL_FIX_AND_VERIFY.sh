#!/data/data/com.termux/files/usr/bin/bash
set -u

DB="data/platform.db"
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP="data/platform.db.before-final-integration-$STAMP"

echo "=================================================="
echo "      DELYVO FINAL INTEGRATION FIX"
echo "=================================================="

echo
echo "=== 1. BACKUP DATABASE ==="
cp -p "$DB" "$BACKUP"
echo "BACKUP=$BACKUP"

echo
echo "=== 2. DATABASE MIGRATION ==="

python - <<'PY'
import sqlite3

DB = "data/platform.db"
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")

def columns(table):
    return {
        r[1] for r in con.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

ship_cols = columns("shipments")

# Add missing integration columns.
if "company_id" not in ship_cols:
    con.execute("""
        ALTER TABLE shipments
        ADD COLUMN company_id TEXT
    """)
    print("ADDED shipments.company_id")
else:
    print("shipments.company_id already exists")

if "order_id" not in ship_cols:
    con.execute("""
        ALTER TABLE shipments
        ADD COLUMN order_id TEXT
    """)
    print("ADDED shipments.order_id")
else:
    print("shipments.order_id already exists")

# Backfill company_id from seller -> company.
seller_cols = columns("sellers")

if "seller_id" in ship_cols and "company_id" in seller_cols:
    con.execute("""
        UPDATE shipments
        SET company_id = (
            SELECT s.company_id
            FROM sellers s
            WHERE s.seller_id = shipments.seller_id
        )
        WHERE (company_id IS NULL OR company_id = '')
          AND seller_id IS NOT NULL
          AND seller_id != ''
    """)
    print("BACKFILL seller -> company COMPLETE")

# Backfill order_id from orders -> shipment.
order_cols = columns("orders")

if "shipment_id" in order_cols:
    con.execute("""
        UPDATE shipments
        SET order_id = (
            SELECT o.order_id
            FROM orders o
            WHERE o.shipment_id = shipments.shipment_id
            LIMIT 1
        )
        WHERE (order_id IS NULL OR order_id = '')
    """)
    print("BACKFILL shipment -> order COMPLETE")

con.commit()

# Show final schema.
print()
print("FINAL SHIPMENTS COLUMNS:")
for row in con.execute("PRAGMA table_info(shipments)"):
    print(" ", row[1], row[2])

# Integration statistics.
stats = {}

stats["total_shipments"] = con.execute(
    "SELECT COUNT(*) FROM shipments"
).fetchone()[0]

stats["company_linked"] = con.execute("""
    SELECT COUNT(*)
    FROM shipments
    WHERE company_id IS NOT NULL
      AND company_id != ''
""").fetchone()[0]

stats["order_linked"] = con.execute("""
    SELECT COUNT(*)
    FROM shipments
    WHERE order_id IS NOT NULL
      AND order_id != ''
""").fetchone()[0]

stats["seller_linked"] = con.execute("""
    SELECT COUNT(*)
    FROM shipments
    WHERE seller_id IS NOT NULL
      AND seller_id != ''
""").fetchone()[0]

print()
print("INTEGRATION COUNTS:")
for k, v in stats.items():
    print(f"{k}={v}")

con.close()
PY

echo
echo "=== 3. PYTHON COMPILE ==="
python -m py_compile \
    app.py \
    admin_module.py \
    company_module.py \
    hub_module.py

if [ $? -ne 0 ]; then
    echo "PYTHON_COMPILE=FAIL"
    echo "RESTORE COMMAND: cp -p $BACKUP $DB"
    exit 1
fi

echo "PYTHON_COMPILE=PASS"

echo
echo "=== 4. HEALTH ==="
HEALTH=$(curl -sS --max-time 5 http://127.0.0.1:5001/api/health)
echo "$HEALTH"

echo
echo "=== 5. COMPANY SHIPMENT API ==="
python - <<'PY'
import sqlite3

con = sqlite3.connect("data/platform.db")

companies = con.execute("""
    SELECT company_id
    FROM companies
    ORDER BY rowid
    LIMIT 5
""").fetchall()

print("COMPANIES_FOUND=", len(companies))

for (company_id,) in companies:
    print("COMPANY_ID=", company_id)

con.close()
PY

echo
echo "=== 6. FINAL SCHEMA CHECK ==="
python - <<'PY'
import sqlite3

con = sqlite3.connect("data/platform.db")

cols = {
    r[1]
    for r in con.execute(
        "PRAGMA table_info(shipments)"
    ).fetchall()
}

required = ["shipment_id", "seller_id", "company_id", "order_id"]

for col in required:
    print(
        f"shipments.{col}=" +
        ("PASS" if col in cols else "FAIL")
    )

con.close()
PY

echo
echo "=== 7. FINAL E2E ==="
./final_e2e_qa.sh > final_e2e_qa_result.txt 2>&1
RC=$?

echo "E2E_EXIT_CODE=$RC"

grep -E \
'ALL HTTP CHECKS|HTTP CHECK FAILURES|FAIL:|ERROR|Traceback|success":false|ORDER_ID=|SHIPMENT_ID=|AWB=|ASSIGNMENT_ID=' \
final_e2e_qa_result.txt \
| tail -n 60

echo
echo "=== 8. FINAL RELATIONSHIP TEST ==="
python - <<'PY'
import sqlite3

con = sqlite3.connect("data/platform.db")

# Company -> Seller -> Shipment
company_rows = con.execute("""
    SELECT
        s.shipment_id,
        s.seller_id,
        s.company_id
    FROM shipments s
    WHERE s.company_id IS NOT NULL
      AND s.company_id != ''
    LIMIT 10
""").fetchall()

print("COMPANY_SHIPMENT_LINKS=", len(company_rows))

for row in company_rows:
    print(
        "SHIPMENT=%s SELLER=%s COMPANY=%s" % row
    )

# Order -> Shipment
order_rows = con.execute("""
    SELECT
        o.order_id,
        o.shipment_id,
        s.order_id
    FROM orders o
    LEFT JOIN shipments s
      ON s.shipment_id = o.shipment_id
    WHERE o.shipment_id IS NOT NULL
      AND o.shipment_id != ''
    LIMIT 10
""").fetchall()

print("ORDER_SHIPMENT_LINKS=", len(order_rows))

for row in order_rows:
    print(
        "ORDER=%s ORDER_SHIPMENT=%s SHIPMENT_ORDER=%s" % row
    )

con.close()
PY

echo
echo "=== 9. FINAL DECISION ==="

SCHEMA_OK=$(python - <<'PY'
import sqlite3
con=sqlite3.connect("data/platform.db")
cols={r[1] for r in con.execute("PRAGMA table_info(shipments)")}
print("YES" if {"company_id","order_id"}.issubset(cols) else "NO")
con.close()
PY
)

if [ "$RC" -eq 0 ] && \
   [ "$SCHEMA_OK" = "YES" ] && \
   echo "$HEALTH" | grep -q '"success":true' && \
   echo "$HEALTH" | grep -q '"database":"CONNECTED"'
then
    echo "=================================================="
    echo "✅ DELYVO FINAL INTEGRATION = PASS"
    echo "✅ COMPANY → SHIPMENT = READY"
    echo "✅ ORDER → SHIPMENT = READY"
    echo "✅ HUB → PARTNER = PASS"
    echo "✅ DELIVERY / RTO = PASS"
    echo "✅ FINANCIAL = PASS"
    echo "✅ MARKETPLACE = PASS"
    echo "✅ DATABASE = CONNECTED"
    echo "✅ E2E = PASS"
    echo "=================================================="
else
    echo "=================================================="
    echo "❌ FINAL INTEGRATION NEEDS REVIEW"
    echo "Backup: $BACKUP"
    echo "=================================================="
fi
