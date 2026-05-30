# Sidewalk & Refreshments Inventory System - Owner's Manual

This manual explains how to use the system for daily operations.

## 1) Logging In

- Open the system URL in your browser.
- Enter your username and password.
- After login, you will land on the **Dashboard**.

## 2) Dashboard Basics

- **Total Sales**: current recorded sales value.
- **Low Stock Items**: number of inventory items at or below reorder threshold.
- **Recent Transactions**: latest stock-in and stock-out activity.
- Use dashboard buttons for quick actions (Cashier POS, Stock In, Stock Out).

## 3) Inventory Management

- Go to **Inventory** to view all items.
- Use **Add Item** to create new inventory records.
- Edit item quantity thresholds and unit details when needed.
- If quantity is low, item is flagged for restocking.

## 4) Recording Stock Movement

- Use **Stock In** when supplies arrive.
- Use **Stock Out** for used, wasted, or spoiled stock.
- Use **Stock Count** to reconcile physical counts with system data.
- Every adjustment is saved in **Transactions** for history tracking.

## 5) Menu and Cashier Workflow

- Go to **Cashier POS** for order processing.
- Add menu items to cart, update quantities, then checkout.
- Set payment method (cash, card, e-wallet) and complete order.
- Update order status: pending -> preparing -> served.
- Customer preview menu is available under **Customer View**.

## 6) Daily Sales Monitoring

- Open **Daily Sales** in the sidebar.
- Review:
  - Today's total sales
  - Today's items sold
  - Sale entries count
  - Last 30 days performance
- Use this page for daily closing and reporting.

## 7) Backup and Safety

- Local mode uses `db.sqlite3`; back this file up regularly.
- For hosted deployment, follow:
  - `BUILDPLAN/Render_Deployment_and_Data_Sync_Guide.md`
- Never share `.env` credentials publicly.

## 8) If Something Goes Wrong

- Check deployment logs first (hosting dashboard logs).
- Restart/redeploy the latest stable commit from GitHub.
- Re-run migrations if needed.
- If data appears missing online, perform fixture import workflow from the deployment guide.

## 9) Current Remaining Work

- Upload/finalize menu item photos to complete visual menu presentation.

