#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="FINAL_UI_READINESS_RESULT.txt"

echo "==================================================" | tee "$OUT"
echo "        DELYVO FINAL UI READINESS TEST" | tee -a "$OUT"
echo "==================================================" | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 1. SERVER ===" | tee -a "$OUT"
curl -sS --max-time 5 http://127.0.0.1:5001/api/health | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 2. UI ROUTES ===" | tee -a "$OUT"

for URL in \
"/" \
"/admin" \
"/admin/login" \
"/admin/dashboard" \
"/admin/partners" \
"/company-dashboard" \
"/hub-dashboard" \
"/partner-dashboard" \
"/seller-dashboard" \
"/delyvo-market"
do
    CODE=$(curl -sS -o /dev/null -w "%{http_code}" \
        --max-time 5 "http://127.0.0.1:5001$URL")
    echo "$URL -> HTTP $CODE" | tee -a "$OUT"
done

echo | tee -a "$OUT"
echo "=== 3. ACTIVE TEMPLATE CHECK ===" | tee -a "$OUT"

for f in \
templates/admin_login.html \
templates/admin_dashboard.html \
templates/admin_partners.html \
templates/company_dashboard.html \
templates/hub_dashboard.html \
templates/partner_dashboard.html \
templates/seller_dashboard.html \
templates/delyvo_market.html \
templates/delyvo_home.html
do
    if [ -f "$f" ]; then
        echo "PASS $f" | tee -a "$OUT"
    else
        echo "FAIL $f" | tee -a "$OUT"
    fi
done

echo | tee -a "$OUT"
echo "=== 4. JAVASCRIPT FETCH/API AUDIT ===" | tee -a "$OUT"

grep -RniE \
'fetch\(|axios\.|/api/|addEventListener|onclick=|onsubmit' \
templates static 2>/dev/null \
| grep -vE 'before-|backup|step' \
| head -n 300 | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 5. FORMS ===" | tee -a "$OUT"

grep -RniE \
'<form|<button|type="submit"|type="button"' \
templates 2>/dev/null \
| grep -vE 'before-|backup|step' \
| head -n 300 | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 6. BROKEN HTML/JS MARKERS ===" | tee -a "$OUT"

grep -RniE \
'undefined|NaN|javascript:void\(0\)|console\.error|throw new Error|alert\("Error|fetch failed' \
templates static 2>/dev/null \
| grep -vE 'before-|backup|step' \
| head -n 150 | tee -a "$OUT" || true

echo | tee -a "$OUT"
echo "=== 7. CORE API SMOKE TEST ===" | tee -a "$OUT"

for URL in \
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
    CODE=$(curl -sS -o /dev/null -w "%{http_code}" \
        --max-time 5 "http://127.0.0.1:5001$URL")
    echo "$URL -> HTTP $CODE" | tee -a "$OUT"
done

echo | tee -a "$OUT"
echo "=== 8. PYTHON COMPILE ===" | tee -a "$OUT"

python -m py_compile \
app.py \
admin_module.py \
company_module.py \
hub_module.py \
&& echo "PYTHON_COMPILE=PASS" | tee -a "$OUT" \
|| echo "PYTHON_COMPILE=FAIL" | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 9. FINAL E2E ===" | tee -a "$OUT"

./final_e2e_qa.sh > final_e2e_qa_result.txt 2>&1
RC=$?

echo "E2E_EXIT_CODE=$RC" | tee -a "$OUT"

grep -E \
'ALL HTTP CHECKS|HTTP CHECK FAILURES|FAIL:|ERROR|Traceback|success":false|ORDER_ID=|SHIPMENT_ID=|AWB=|ASSIGNMENT_ID=' \
final_e2e_qa_result.txt \
| tail -n 60 | tee -a "$OUT"

echo | tee -a "$OUT"
echo "=== 10. FINAL UI DECISION ===" | tee -a "$OUT"

if \
curl -sS --max-time 5 http://127.0.0.1:5001/api/health \
| grep -q '"success":true'
then
    HEALTH_OK=1
else
    HEALTH_OK=0
fi

if [ "$RC" -eq 0 ] && [ "$HEALTH_OK" -eq 1 ]; then
    echo "==================================================" | tee -a "$OUT"
    echo "✅ UI/BACKEND READINESS BASELINE = PASS" | tee -a "$OUT"
    echo "==================================================" | tee -a "$OUT"
else
    echo "==================================================" | tee -a "$OUT"
    echo "❌ UI/BACKEND READINESS = NEEDS REVIEW" | tee -a "$OUT"
    echo "==================================================" | tee -a "$OUT"
fi

echo
echo "RESULT SAVED: $OUT"
