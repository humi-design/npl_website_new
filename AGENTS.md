# AGENTS.md

## Project
Nirmal Precision marketing website + admin panel.
Single-file Flask app: `app.py` (~2100 lines) containing all CRM models and routes,
with Jinja templates in `templates/`. MySQL via Flask-SQLAlchemy (`pymysql`).
There is no test infrastructure and no local MySQL in the dev sandbox; use SQLite
with `db.create_all()` for isolated verification.

## Conventions
- Admin routes live under `/admin/...` and gate on `session.get("admin")`.
- Existing admin pages are standalone HTML files: each repeats its own inline
  `<style>` block and sidebar nav. When adding an admin page, copy that pattern
  and add the nav link to `templates/admin*.html` (all of them).
- Deploy path is Passenger (`passenger_wsgi.py`). Runtime deps are listed in
  `requirements.txt`.

## Invoice Generator
`invoices.py` is a self-contained module. It exposes
`create_invoice_blueprint(db, crm_models=...)`, registered at the bottom of
`app.py`. CRM models are injected (not imported) to avoid a circular import.

Key invariants:
- Invoice tables are separate from CRM tables (`migrate_invoices.sql`).
- Each invoice stores its own snapshot of exporter/consignee/shipping/items.
  Company defaults (`invoice_defaults`) only pre-fill new invoices and never
  mutate saved ones.
- Editing a `Generated` invoice creates a new revision and preserves the
  original (revisions are unique per `invoice_number`).
- `templates/invoice_pdf.html` is the single design used for both the on-screen
  Preview and the downloaded PDF (via `xhtml2pdf`), so they stay identical.
- PDF filename is `INVOICE_NUMBER.pdf` (revisions append `_R<n>`).
