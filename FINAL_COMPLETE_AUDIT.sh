#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "=================================================="
echo "        DELYVO FINAL COMPLETE AUDIT"
echo "=================================================="

echo
echo "=== 1. PYTHON COMPILE ==="
python -m py_compile \
  app.py \
  admin_module.py \
  company_module.py \
  hub_module.py

if [ $? -eq 0 ]; then
  echo "PYTHON_COMPILE=PASS"
else
  echo "PYTHON_COMPILE=FAIL"
  exit 1
fi

echo
echo "=== 2. DATABASE ==="
python - <<'PY'
import sqlite3

db = "data/platform.db"
con = sqlite3.connect(db)

tables = {
    r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
}

required = {
    "admins",
    "companies",
    "sellers",
    "products",
    "orders",
    "order_items",
    "shipments",
    "shipment_events",
    "hubs",
    "bags",
    "bag_shipments",
    "hub_movements",
    "delivery_partners",
    "delivery_assignments",
    "partner_seats",
    "payments",
    "partner_earnings",
    "seller_settlements",
    "company_settlements",
    "platform_transactions",
    "financial_settings",
    "owner_ledger",
    "owner_withdrawals",
}

missing = sorted(required - tables)

print("TABLE_COUNT=", len(tables))

if missing:
    print("MISSING_TABLES=", ",".join(missing))
else:
    print("REQUIRED_TABLES=PASS")

# Important relationship columns
checks = {
    "sellers.company_id": ("sellers", "company_id"),
    "shipments.company_id": ("shipments", "company_id"),
    "shipments.seller_id": ("shipments", "seller_id"),
    "shipments.order_id": ("shipments", "order_id"),
    "orders.shipment_id": ("orders", "shipment_id"),
    "delivery_assignments.partner_id": ("delivery_assignments", "partner_id"),
    "delivery_assignments.shipment_id": ("delivery_assignments", "shipment_id"),
    "delivery_assignments.hub_code": ("delivery_assignments", "hub_code"),
}

for label, (table, col) in checks.items():
    cols = {
        r[1] for r in con.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }
    print(
        f"{label}=" +
        ("PASS" if col in cols else "MISSING")
    )

con.close()
PY

echo
echo "=== 3. SERVER HEALTH ==="
HEALTH=$(curl -sS --max-time 5 http://127.0.0.1:5001/api/health)
echo "$HEALTH"

echo
echo "=== 4. ROUTES ==="
echo "app.py=$(grep -cE '@app\.route' app.py)"
echo "admin_module.py=$(grep -cE '@app\.route' admin_module.py)"
echo "company_module.py=$(grep -cE '@app\.route' company_module.py)"
echo "hub_module.py=$(grep -cE '@app\.route' hub_module.py)"

echo
echo "=== 5. ACTIVE UI ==="
for f in \
templates/admin_dashboard.html \
templates/admin_login.html \
templates/admin_partners.html \
templates/company_dashboard.html \
templates/hub_dashboard.html \
templates/partner_dashboard.html \
templates/seller_dashboard.html \
templates/delyvo_market.html \
templates/delyvo_home.html \
static/admin_partners.css \
static/hub_app.css \
static/partner_app.css \
static/partner_dashboard.css
do
    [ -f "$f" ] && echo "PASS $f" || echo "MISSING $f"
done

echo
echo "=== 6. CORE API GROUPS ==="
for p in \
"/api/admin" \
"/api/sellers" \
"/api/companies" \
"/api/shipments" \
"/api/hubs" \
"/api/bags" \
"/api/movements" \
"/api/partners" \
"/api/assignments" \
"/api/payments" \
"/api/financial" \
"/api/owner" \
"/api/market"
do
    COUNT=$(grep -RohE "\"$p[^\" ]*" \
      app.py admin_module.py company_module.py hub_module.py 2>/dev/null \
      | sort -u | wc -l)
    echo "$p=$COUNT"
done

echo
echo "=== 7. COMPANY INTEGRATION ==="
grep -nEi \
'company_id|companies/.*/shipments|company.*dashboard' \
app.py company_module.py \
| grep -vE 'before-|backup|step' \
| tail -n 80

echo
echo "=== 8. ORDER → SHIPMENT ==="
grep -nEi \
'order_id|shipment_id|create_shipment' \
app.py \
| grep -vE 'before-|backup|step' \
| tail -n 100

echo
echo "=== 9. HUB → PARTNER ==="
grep -nEi \
'hub_code|partner_id|assignment_id' \
app.py \
| grep -vE 'before-|backup|step' \
| tail -n 100

echo
echo "=== 10. DELIVERY FLOW ==="
grep -nEi \
'pickup|deliver|rto|returned|OUT_FOR_DELIVERY|DELIVERED' \
app.py \
| grep -vE 'before-|backup|step' \
| tail -n 120

echo
echo "=== 11. FINANCIAL FLOW ==="
grep -nEi \
'payment|cod|earning|settlement|payout|owner_ledger|withdraw' \
app.py \
| grep -vE 'before-|backup|step' \
| tail -n 140

echo
echo "=== 12. MARKETPLACE ==="
grep -nEi \
'/api/market|market.*order|seller.*order|order.*seller' \
app.py templates/delyvo_market.html \
| grep -vE 'before-|backup|step' \
| tail -n 120

echo
echo "=== 13. E2E ==="
./final_e2e_qa.sh > final_e2e_qa_result.txt 2>&1
RC=$?

echo "E2E_EXIT_CODE=$RC"

grep -E \
'ALL HTTP CHECKS|HTTP CHECK FAILURES|FAIL:|ERROR|Traceback|success":false|ORDER_ID=|SHIPMENT_ID=|AWB=|ASSIGNMENT_ID=' \
final_e2e_qa_result.txt \
| tail -n 50

echo
echo "=== 14. FINAL ERROR SCAN ==="
ERRORS=$(grep -RniE \
'TODO|FIXME|COMING SOON|NOT IMPLEMENTED|Traceback|ERROR' \
app.py admin_module.py company_module.py hub_module.py templates static \
2>/dev/null \
| grep -vE 'before-|backup|step|placeholder' \
| head -n 50)

if [ -z "$ERRORS" ]; then
    echo "ERROR_SCAN=PASS"
else
    echo "$ERRORS"
fi

echo
echo "=================================================="
if [ "$RC" -eq 0 ] && \
   echo "$HEALTH" | grep -q '"success":true' && \
   echo "$HEALTH" | grep -q '"database":"CONNECTED"'; then
    echo "✅ DELYVO FINAL SYSTEM AUDIT = PASS"
    echo "✅ BACKEND = READY"
    echo "✅ DATABASE = CONNECTED"
    echo "✅ E2E = PASS"
else
    echo "❌ DELYVO FINAL SYSTEM AUDIT = NEEDS FIX"
fi
echo "=================================================="
