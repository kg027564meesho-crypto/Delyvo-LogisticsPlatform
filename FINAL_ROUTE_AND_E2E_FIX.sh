#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "=================================================="
echo "       DELYVO FINAL ROUTE + E2E FIX"
echo "=================================================="

cp -p app.py "app.py.before-route-e2e-fix-$(date +%Y%m%d_%H%M%S)"

echo
echo "=== 1. CURRENT ROUTES ==="
python - <<'PY'
from app import app

for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
    if any(x in str(rule) for x in [
        "admin", "seller", "hub", "assignment", "shipment"
    ]):
        print(f"{','.join(sorted(rule.methods)):<25} {rule}")
PY

echo
echo "=== 2. CHECK E2E ASSIGNMENT PAYLOAD ==="
grep -nE \
'api/hubs/.*/assign|/status|assign.*json|status.*json|assignment' \
final_e2e_qa.sh \
| grep -vE 'before-|backup|step' \
| head -n 120

echo
echo "=== 3. CHECK ASSIGNMENT ROUTE IMPLEMENTATION ==="
grep -RniE \
'@app\.route.*hubs/.*/assign|def .*assign|hubs/.*/assign' \
app.py hub_module.py \
| grep -vE 'before-|backup|step' \
| head -n 120

echo
echo "=== 4. CHECK SHIPMENT STATUS IMPLEMENTATION ==="
grep -RniE \
'@app\.route.*shipments/.*/status|def .*shipment.*status|shipment.*status' \
app.py hub_module.py \
| grep -vE 'before-|backup|step' \
| head -n 160

echo
echo "=== 5. TEST EXISTING UI ROUTES ==="
for URL in \
"/" \
"/admin" \
"/admin-dashboard" \
"/admin-partners" \
"/company" \
"/company-dashboard" \
"/hub-dashboard" \
"/partner-dashboard" \
"/market"
do
    CODE=$(curl -sS -o /dev/null -w "%{http_code}" \
        --max-time 5 "http://127.0.0.1:5001$URL")
    echo "$URL -> HTTP $CODE"
done

echo
echo "=== 6. PYTHON COMPILE ==="
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
echo "=================================================="
echo "IMPORTANT:"
echo "400 errors will NOT be hidden or marked PASS."
echo "Use the payload/route information above to fix"
echo "the real assignment/status contract."
echo "=================================================="
