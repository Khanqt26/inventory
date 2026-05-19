# Online Deployment Checklist (School Demo on Render)

## Goal
Deploy the Sidewalk & Refreshments Django POS online for professor checking:
- Public URL (easy to open in browser)
- Fast setup
- Free tier friendly
- Works reliably for demo and grading

---

## 0. What This Setup Is For
- [ ] Class demo / portfolio use (not full production)
- [ ] Free tier constraints accepted:
  - [ ] Service may sleep when idle
  - [ ] First load can take around 30-60 seconds
- [ ] SQLite is acceptable for school demo

---

## 1. Local Project Prep
- [ ] Verify project runs locally
  - [ ] `python manage.py check`
  - [ ] `python manage.py runserver`
- [ ] Ensure dependencies are updated in `requirements.txt`
- [ ] Ensure `Procfile` exists with:
  - [ ] `web: gunicorn config.wsgi:application`
- [ ] Ensure static files are production-ready (WhiteNoise configured)
- [ ] Commit and push latest code to GitHub

---

## 2. Create Render Web Service
- [ ] Create/sign in to Render account: `https://render.com`
- [ ] Click `New +` -> `Web Service`
- [ ] Connect GitHub repository: `restaurant_inventory`
- [ ] Select branch to deploy (usually `main`)

### Render Build/Start Commands
- [ ] Build Command:
  - [ ] `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- [ ] Start Command:
  - [ ] `gunicorn config.wsgi:application`

---

## 3. Render Environment Variables
Set these in Render -> Service -> `Environment`:

- [ ] `DJANGO_SECRET_KEY=<long-random-secret>`
- [ ] `DJANGO_DEBUG=False`
- [ ] `USE_SQLITE=True`
- [ ] `DJANGO_ALLOWED_HOSTS=<your-service-name>.onrender.com`
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-service-name>.onrender.com`
- [ ] `DJANGO_TIME_ZONE=Asia/Manila`
- [ ] `DJANGO_SECURE_SSL_REDIRECT=True`
- [ ] `DJANGO_SESSION_COOKIE_SECURE=True`
- [ ] `DJANGO_CSRF_COOKIE_SECURE=True`
- [ ] `DJANGO_SECURE_HSTS_SECONDS=31536000`
- [ ] `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False`
- [ ] `DJANGO_SECURE_HSTS_PRELOAD=False`

Notes:
- [ ] Replace `<your-service-name>` with actual Render service name.
- [ ] Do not commit real `.env` secrets to GitHub.

---

## 4. First Deploy and Admin Setup
- [ ] Click `Create Web Service`
- [ ] Wait for deploy status `Live`
- [ ] Open Render Shell and create admin user:
  - [ ] `python manage.py createsuperuser`
- [ ] (Optional) Load sample data for easier checking/demo

---

## 5. Verification Before Sending to Professor
- [ ] Open app URL: `https://<your-service-name>.onrender.com`
- [ ] Test login page
- [ ] Test admin: `/admin`
- [ ] Test cashier/POS flow
- [ ] Confirm static files load (CSS/JS/images)
- [ ] Do one full test transaction flow

---

## 6. Submission-Ready Package
- [ ] Share public URL with professor
- [ ] Share test account credentials (if required)
- [ ] Share short usage note:
  - [ ] "If site is sleeping, please wait about 30-60 seconds on first load."
- [ ] Keep one backup screen recording of working demo

---

## 7. Quick Troubleshooting
- [ ] If deploy fails, open `Logs` in Render and check first error line
- [ ] If `DisallowedHost` appears:
  - [ ] Recheck `DJANGO_ALLOWED_HOSTS`
- [ ] If CSRF error appears:
  - [ ] Recheck `DJANGO_CSRF_TRUSTED_ORIGINS` includes `https://...`
- [ ] If CSS is broken:
  - [ ] Ensure `collectstatic` ran successfully in build logs
- [ ] If app crashes after update:
  - [ ] Trigger `Manual Deploy` -> `Clear build cache & deploy`

---

## 8. After-Grading Upgrade Path (Optional)
For real-world use later, migrate to:
- Ubuntu VPS
- PostgreSQL
- Gunicorn + Nginx
- Custom domain and full ops backups

Keep this file focused on school/demo deployment for now.
