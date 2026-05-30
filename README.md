# Sidewalk & Refreshments Inventory System

A Django-based inventory and sales management system for a small restaurant/canteen setup.  
This project supports stock monitoring, menu/cashier operations, and daily sales tracking.

## Project Overview

This system was built to help manage:
- Inventory records and stock movement
- Menu and category organization
- Cashier POS workflow with checkout
- Low-stock alerts and restock actions
- Daily sales reporting

## Current Features

- Authentication-protected admin dashboard
- Inventory CRUD (create, view, update, delete)
- Stock In / Stock Out / Stock Count Adjustment
- Transaction history logs
- Category management
- Menu item browsing and order recording
- Cashier POS:
  - cart add/update/remove
  - checkout with payment method
  - order status updates (`pending`, `preparing`, `served`)
- Low-stock alert system:
  - active, snoozed, acknowledged views
  - quick acknowledge/snooze actions
- Daily sales page:
  - today summary
  - last 30 days totals
  - recent sales feed

## Tech Stack

- Python 3
- Django
- SQLite (default local database)
- PostgreSQL-ready configuration for deployment
- WhiteNoise for static files in production

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/Khanqt26/inventory.git
cd inventory
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
- Copy `.env.example` to `.env` and update values as needed.
- For local development, `DJANGO_DEBUG=True` is enabled.

5. Run migrations:
```bash
python manage.py migrate
```

6. Create admin account:
```bash
python manage.py createsuperuser
```

7. Start server:
```bash
python manage.py runserver
```

8. Open in browser:
- App: `http://127.0.0.1:8000/`
- Django Admin: `http://127.0.0.1:8000/admin/`

## Important Routes

- `/dashboard/` - main dashboard
- `/cashier/` - cashier POS
- `/sales/daily/` - daily sales report
- `/inventory/` - inventory list
- `/stock-in/` - record stock in
- `/stock-out/` - record stock out
- `/transactions/` - stock transaction history
- `/customer/` - public customer menu preview

## Database Notes

- Default local database: `db.sqlite3`
- Database switching is controlled in `config/settings.py` using:
  - `USE_SQLITE=True` (SQLite)
  - `USE_SQLITE=False` + `POSTGRES_*` vars (PostgreSQL)

## Deployment Notes

- Repository is deployable on Render/Railway-like platforms.
- Ensure environment variables are set correctly in your hosting service.
- Run migrations during deploy:
```bash
python manage.py migrate
```
- Collect static files when required:
```bash
python manage.py collectstatic --noinput
```

## Project Status

Current branch includes Daily Sales reporting update:
- Commit: `f3826a5`
- Feature: Daily Sales page + navigation integration

## Submission Note

For academic submission:
- Include this repository link
- Submit documentation in research format
- Include deployment URL and screenshots/evidence of testing

## License

This project is for educational use.

