# Sidewalk & Refreshments Integrated POS and Inventory Management System:
## Design, Development, and Operational Evaluation

**Author:** Khan L. Adjarani  
**Institution:** [Your School Name]  
**Course/Program:** [Your Course/Program]  
**Date:** May 30, 2026

---

## Abstract
Small food businesses often rely on manual inventory and sales tracking, which causes stock inaccuracies, delayed reporting, and avoidable stock-outs. This study presents the design and implementation of a web-based Integrated Point-of-Sale (POS) and Inventory Management System for Sidewalk & Refreshments. The system was developed using Django and deployed with cloud-ready configuration to support both local and hosted operation. Core modules include authentication, category and inventory management, stock movement recording, cashier checkout workflow, low-stock alerting, transaction history, customer menu display, and daily sales reporting.

The project followed a phased software engineering workflow: requirements definition, model design, feature implementation, iterative testing, and deployment preparation. Evaluation through manual functional testing showed that the system supports end-to-end operations: order processing updates inventory atomically, low-stock conditions are detected and tracked, and dashboard/reporting components provide daily operational visibility. The system reduced manual recording steps, improved stock traceability, and produced actionable daily sales summaries.

Results indicate that the proposed solution is suitable for small-scale restaurant operations and can serve as a baseline for future enhancements such as role-based access control, advanced analytics, receipt printing, and multi-branch synchronization.

**Keywords:** POS, inventory management, Django, low-stock alert, daily sales, small business information system

---

## 1. Introduction

### 1.1 Background of the Study
Many small restaurants and refreshment stores manage stock and sales with notebooks or spreadsheet files. While simple at first, this practice becomes difficult when transaction volume increases. Missing entries, late updates, and inconsistent counting often lead to inaccurate inventory levels and delayed restocking decisions.

Sidewalk & Refreshments required a lightweight but structured system that could connect cashier operations with inventory movement in real time. A web-based solution was selected to centralize operations and enable easier expansion to cloud deployment.

### 1.2 Problem Statement
The business faced operational risks common to manual workflows:
1. Difficulty tracking stock movement consistently across days.
2. Limited visibility of low-stock items before shortages occur.
3. Fragmented sales and inventory records.
4. Lack of a simple daily sales summary for owner review.

### 1.3 Objectives of the Study
The general objective was to develop and evaluate an integrated POS and inventory system for Sidewalk & Refreshments.

Specific objectives were to:
1. Build a centralized platform for menu, cashier, and inventory operations.
2. Record stock-in and stock-out transactions with validation controls.
3. Provide low-stock alerting and inventory monitoring tools.
4. Implement daily sales reporting for operational decision-making.
5. Prepare documentation and deployment workflow for project handover.

### 1.4 Scope and Delimitation
The study focused on a single-branch setup and core restaurant operations:
- Inventory CRUD and stock movement logs
- Cashier cart and checkout flow
- Menu categorization and customer-facing menu view
- Dashboard and daily sales reporting
- Cloud deployment readiness and data sync documentation

Out of scope:
- Hardware integration (barcode scanners, automatic receipt printers)
- Full accounting integration
- Native mobile app
- Multi-branch centralized synchronization

### 1.5 Significance of the Study
The project benefits:
- **Owner/Manager:** better visibility of sales and stock health.
- **Cashier/Staff:** faster and more consistent order-to-inventory workflow.
- **Future Developers:** structured baseline for continued feature expansion.

---

## 2. Review of Related Literature and Systems

Small business POS and inventory systems typically emphasize transaction speed, stock accuracy, and usability. Existing literature and practice show that integrating sales with inventory updates reduces discrepancy between recorded and actual stock levels. Real-time or near-real-time stock deduction during checkout helps prevent over-selling and supports better reorder planning.

Web frameworks such as Django are widely used in academic and small business systems because they provide built-in authentication, ORM-based data modeling, and rapid CRUD development. For low-resource environments, SQLite is practical for local deployment while PostgreSQL supports scalability in hosted production environments. These principles informed the system architecture and deployment strategy used in this project.

---

## 3. Methodology

### 3.1 Research and Development Approach
The project used a development-oriented methodology aligned with iterative prototyping:
1. Requirement gathering and workflow mapping.
2. Data model and module planning.
3. Incremental feature implementation by phase.
4. Manual functional testing and validation.
5. Deployment preparation and documentation.

### 3.2 System Development Environment
- **Backend:** Python, Django
- **Frontend:** Django templates with HTMX-enhanced interactions
- **Database:** SQLite (local default), PostgreSQL-ready configuration
- **Version Control:** Git and GitHub
- **Deployment Target:** Cloud-ready setup (Render workflow documented)

### 3.3 System Design
Major data entities:
- `Category`
- `InventoryItem`
- `StockTransaction`
- `MenuItem`
- `Recipe`
- `Sale`
- `CustomerOrder`
- `CustomerOrderLine`
- `InventorySettings`
- `LowStockAlert`

Core process design:
1. Cashier creates and checks out orders.
2. Sales entries are recorded.
3. Linked recipe items are deducted from inventory using atomic updates.
4. Low-stock checks trigger alerts when thresholds are crossed.
5. Dashboard and daily sales pages display operational summaries.

### 3.4 Testing Procedure
Manual test scenarios were executed per module:
- Authentication and session redirection
- Inventory create/update/delete correctness
- Stock-in and stock-out validation (including negative stock prevention)
- POS cart/checkout flow and order status updates
- Alert generation and acknowledgment/snooze actions
- Daily sales page summaries and historical rollups

Validation checks included `python manage.py check` and workflow-level consistency checks between sales and inventory movement records.

---

## 4. Results and Discussion

### 4.1 Implemented System Features
The system delivered the planned modules:
1. Secure login/logout and protected admin workflows.
2. Inventory management with category filters and low-stock indicators.
3. Stock movement recording with transaction history and auditability.
4. Cashier POS with cart operations, checkout, payment method capture, and order status progression.
5. Low-stock alerts with active, snoozed, and acknowledged states.
6. Public customer menu view.
7. Daily sales report page with today summary, recent sales, and 30-day totals.

### 4.2 Operational Improvements Observed
Compared with manual recording, the implemented system improved:
- **Traceability:** every stock movement is logged with timestamp and notes.
- **Consistency:** checkout workflow directly records sales and updates stock.
- **Visibility:** dashboard and daily sales report provide immediate status overview.
- **Control:** stock-out validation prevents negative inventory records.

### 4.3 Limitations
Despite the improvements, current limitations include:
1. Menu image completion is still pending for some items.
2. Advanced analytics (weekly/monthly trend charts) are minimal.
3. No automated backup scheduler inside the app itself.
4. Single-branch focus only.

### 4.4 Discussion
The results align with the project objectives: the system is functional, deployable, and suitable for small business daily operations. Integration between POS and inventory is the primary strength, because it addresses the root problem of fragmented records. The addition of daily sales reporting further supports owner-level decision-making and end-of-day review.

---

## 5. Conclusion and Recommendations

### 5.1 Conclusion
This study successfully designed and developed an Integrated POS and Inventory Management System for Sidewalk & Refreshments. The implemented platform addresses key operational challenges in manual stock and sales tracking by centralizing records, automating inventory deduction during sales, and providing actionable low-stock and daily sales insights.

The project demonstrates that a Django-based solution can effectively support small restaurant operations with limited technical overhead while maintaining a clear path toward production deployment and future scaling.

### 5.2 Recommendations
For immediate completion and next-phase improvements, it is recommended to:
1. Finalize and upload complete menu item images.
2. Add exportable sales reports (CSV/PDF) for formal record keeping.
3. Implement role-based permissions for owner, cashier, and viewer accounts.
4. Add automated backup scheduling and restore verification routine.
5. Expand reporting with weekly/monthly analytics and top-selling item insights.

---

## References

1. Django Software Foundation. (2026). *Django Documentation*. https://docs.djangoproject.com/  
2. Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures* (Doctoral dissertation, University of California, Irvine).  
3. Sommerville, I. (2016). *Software Engineering* (10th ed.). Pearson.  
4. Pressman, R. S., & Maxim, B. R. (2020). *Software Engineering: A Practitioner’s Approach* (9th ed.). McGraw-Hill.  
5. Elmasri, R., & Navathe, S. B. (2016). *Fundamentals of Database Systems* (7th ed.). Pearson.

---

## Appendix A - Project Repository

GitHub Repository: https://github.com/Khanqt26/inventory

## Appendix B - Suggested Submission Attachments

- Screenshot of Dashboard
- Screenshot of Cashier POS checkout flow
- Screenshot of Daily Sales page
- Screenshot of Inventory and low-stock alerts
- Deployment URL screenshot / status proof

