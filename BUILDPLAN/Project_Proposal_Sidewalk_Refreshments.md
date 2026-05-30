# Project Proposal
**Project Title:** Sidewalk & Refreshments Integrated POS and Inventory Management System  
**Prepared For:** Sidewalk & Refreshments  
**Prepared By:** [Your Name / Team]  
**Date:** April 29, 2026

## 1. Executive Summary
This proposal presents a complete web-based POS and inventory system tailored for Sidewalk & Refreshments. The system centralizes menu management, cashier operations, stock control, low-stock monitoring, and audit reporting into one platform. It is designed to improve daily operations, reduce manual errors, and provide better stock visibility for decision-making.

The current build already includes core production-ready modules (Cashier POS, inventory movement, low-stock alerts, customer menu, menu audit, stock count adjustment), and this proposal formalizes scope, outcomes, and next enhancement phases.

## 2. Project Objectives
- Digitize cashier and stock operations in one system.
- Track inventory movement in real time.
- Prevent stock-outs through alerts and threshold controls.
- Improve order processing speed and consistency.
- Maintain auditability of stock and menu changes.
- Provide management visibility through dashboard and reports.

## 3. Scope of Work
### In Scope
- Web-based system for admin, cashier, and public menu view.
- POS order processing with cart and checkout.
- Inventory item management and stock movement logging.
- Low-stock alerting and acknowledgment workflow.
- Menu availability controls and public-facing status display.
- Menu quality/audit diagnostics tools.
- Physical count adjustment workflow.

### Out of Scope (Current Phase)
- Hardware integration (barcode scanner, thermal printer auto-driver).
- Multi-branch centralized synchronization.
- Accounting software integration.
- Mobile native app deployment.

## 4. Proposed System Architecture
- **Backend:** Django (Python)
- **Frontend:** Django templates + HTMX-enhanced interactions
- **Database:** SQLite (current), with path to PostgreSQL for production scale
- **Authentication:** Django authentication (admin/cashier access)
- **Deployment Readiness:** Local deployment now, cloud-deployable structure

## 5. Functional Feature Matrix
| Module | Feature | Description | Status |
|---|---|---|---|
| Authentication | Admin Login/Logout | Secure admin access and session handling | Implemented |
| Dashboard | KPI Summary | Total sales, low-stock count, inventory count, stock health | Implemented |
| Dashboard | Quick Actions | Fast access to POS, stock in/out, customer view, restock | Implemented |
| Dashboard | Low Stock Panel | List low-stock items with restock action | Implemented |
| Dashboard | Alert Panel | Active/snoozed/acknowledged alert filtering | Implemented |
| Dashboard | Transactions Feed | Recent inventory movement records | Implemented |
| POS | Cashier POS Page | Menu grid + cart + checkout workflow | Implemented |
| POS | Cart Management | Add/update/remove quantity in cart | Implemented |
| POS | Checkout | Creates order, line items, and sales records | Implemented |
| POS | Payment Method | Cash/Card/E-wallet capture during checkout | Implemented |
| POS | Order Status Lifecycle | Pending -> Preparing -> Served (+ reopen) | Implemented |
| POS | Availability Toggle | Mark items available/unavailable directly in POS | Implemented |
| POS | Visibility Filters | Available / Unavailable / All menu filter | Implemented |
| Inventory | Item CRUD | Create/update/delete inventory items | Implemented |
| Inventory | Stock In | Record added stock with notes | Implemented |
| Inventory | Stock Out | Record deducted stock with validation | Implemented |
| Inventory | Restock Actions | Per-item restock and bulk restock | Implemented |
| Inventory | Stock Count Adjustment | Physical count bulk adjustment with transaction logs | Implemented |
| Inventory | Transaction History | Full and per-item movement history | Implemented |
| Alerts | Threshold Logic | Auto-detect low stock based on reorder threshold | Implemented |
| Alerts | Alert Events | LowStockAlert records with trigger metadata | Implemented |
| Alerts | Acknowledge/Snooze | Mark handled or snooze 24h | Implemented |
| Alerts | User Attribution | Tracks who acknowledged/snoozed | Implemented |
| Alerts | Settings | Enable/disable low-stock alerts and default threshold | Implemented |
| Menu | Category Filters | Filter menu by category (public/admin/POS) | Implemented |
| Menu | Customer View | Public menu cards with available/unavailable status | Implemented |
| Menu | Menu Sync Basis | Structured official menu loaded and normalized | Implemented |
| Menu Audit | Duplicate Detection | Detect duplicate category+item names | Implemented |
| Menu Audit | Coverage Check | Missing required categories and empty categories | Implemented |
| Menu Audit | Range-price Review | Identify items using range-price notes | Implemented |
| Menu Audit | Unavailable List | Review all unavailable menu items | Implemented |
| UX | In-page Navigation | HTMX-enhanced reduced full page reload behavior | Implemented |
| UX | Loading Overlay | Spinner overlay on in-page interactions | Implemented |
| UX | Scroll Preservation | Keeps scroll position during HTMX swaps | Implemented |

## 6. Business Benefits
- Faster cashier operations and reduced manual logging.
- Better visibility of stock usage and reorder needs.
- Reduced risk of selling unavailable items.
- Stronger control over menu consistency and data quality.
- Audit trail for operational accountability.
- Foundation ready for scaling and integrations.

## 7. Risks and Mitigation
- **Risk:** Inventory values currently placeholder/demo.  
  **Mitigation:** Use Stock Count Adjustment after physical inventory count.
- **Risk:** Staff adoption and process consistency.  
  **Mitigation:** Quick training + SOP for stock in/out and order status updates.
- **Risk:** Single-device/database limitations at higher volume.  
  **Mitigation:** Migrate to PostgreSQL + managed hosting in next phase.

## 8. Recommended Next Phase
1. Kitchen Board view (production queue screen).
2. Receipt/print-friendly order summary.
3. Role-based permissions (manager/cashier/viewer).
4. Daily/weekly sales and stock analytics reports.
5. Optional cloud deployment + backup strategy.

## 9. Implementation Plan (Suggested)
- **Phase 1 (Done):** Core POS + inventory + alerts + menu audit.
- **Phase 2:** Kitchen workflow + receipts + reporting.
- **Phase 3:** Security hardening + production deployment + training.

## 10. Acceptance Criteria
- Cashier can process end-to-end orders with status updates.
- Inventory updates correctly via POS recipes and stock forms.
- Low-stock alerts trigger and can be managed.
- Public customer menu reflects item availability state.
- Audit/report pages accurately reflect current system data.
