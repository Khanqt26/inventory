# Render Deployment and Data Sync Guide (Django)

## Purpose
Use this guide for:
- Updating live site code on Render
- Syncing local database data to live Render PostgreSQL
- Avoiding common mistakes (empty data, repeated imports, build failures)

---

## A. One-Time Setup (Already Done)
- Render Web Service is connected to GitHub repo.
- Render PostgreSQL is created.
- App env vars are set (`POSTGRES_*`, `USE_SQLITE=False`, Django security vars).

---

## B. When You Change Code
If you edit Python/templates/CSS/JS:

1. Commit and push:
```powershell
git add .
git commit -m "describe your change"
git push
```
2. Render auto-deploys (or trigger Manual Deploy).
3. Live site updates after deploy succeeds.

Notes:
- Code updates sync automatically.
- Local database content does not sync automatically.

---

## C. When You Change Local Data and Need It Online
If you add/edit users, menu items, categories, inventory, etc. in local DB and want same data online:

### 1. Export local data fixture
```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions | Out-File -FilePath data.json -Encoding utf8
```

### 2. Remove UTF-8 BOM (important)
```powershell
@'
from pathlib import Path
p = Path("data.json")
text = p.read_text(encoding="utf-8-sig")
p.write_text(text, encoding="utf-8")
print("BOM removed")
'@ | .\.venv\Scripts\python.exe -
```

### 3. Commit and push fixture
```powershell
git add data.json
git commit -m "Update data fixture for Render import"
git push
```

### 4. Temporary Render Build Command (import step)
Set Build Command to:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py loaddata data.json && python manage.py collectstatic --noinput
```

### 5. Deploy once
- Manual Deploy -> Deploy latest commit
- Confirm logs show fixture import success.

### 6. Revert Build Command (very important)
After successful import, set Build Command back to:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```
- Deploy again.

Why revert:
- Prevents re-import attempt every deploy.
- Avoids duplicate/conflict errors later.

---

## D. If `/admin` or pages show `Bad Request (400)`
Check env vars:
- `DJANGO_ALLOWED_HOSTS=your-service.onrender.com,.onrender.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service.onrender.com,https://*.onrender.com`

Then redeploy.

---

## E. If Live Site Is Empty
Usually means Postgres has no imported data yet.

Fix:
1. Ensure `data.json` is pushed to GitHub.
2. Run one deploy with `loaddata` in Build Command (Section C).
3. Revert Build Command after successful import.

---

## F. Security Reminders
- Do not commit `.env` or secrets.
- If a DB password is exposed, rotate it immediately and update `POSTGRES_PASSWORD`.
- Remove `DJANGO_SUPERUSER_*` env vars after initial admin setup.

---

## G. Quick Commands Reference
Code update:
```powershell
git add .
git commit -m "update"
git push
```

Data export:
```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions | Out-File -FilePath data.json -Encoding utf8
```

---

## H. Rule of Thumb
- Code change -> push -> auto deploy.
- Data change (local DB) -> export/import workflow required.
