"""
Invoice Generator module for the Nirmal Precision admin panel.

This module is self-contained and is registered onto the existing Flask app as
a blueprint. It does not modify any existing CRM models or routes. Invoice data
is kept in its own tables so that issued invoices are immutable snapshots and
are never affected by later changes to CRM data or company defaults.
"""

import io
import json
import os
from datetime import datetime, date

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    send_file,
    jsonify,
)
from werkzeug.utils import secure_filename

# ============================================================================
# CONSTANTS
# ============================================================================

CURRENCIES = ["USD", "EUR", "GBP", "INR"]

# Currency -> (major unit singular, major unit plural, minor unit singular, minor plural)
CURRENCY_WORDS = {
    "USD": ("Dollar", "Dollars", "Cent", "Cents"),
    "EUR": ("Euro", "Euros", "Cent", "Cents"),
    "GBP": ("Pound", "Pounds", "Penny", "Pence"),
    "INR": ("Rupee", "Rupees", "Paise", "Paise"),
}

INVOICE_STATUSES = ["Draft", "Generated"]

SIGNATURE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

# Default company information for Nirmal Precision. These are only used to
# pre-fill new invoices / defaults -- they are editable and never hard-coded
# into the PDF rendering logic.
NIRMAL_DEFAULTS = {
    "exporter_name": "Nirmal Precision Pvt Ltd",
    "address_line1": "4, Jai Matadi Ind. Estate",
    "address_line2": "Opp. Ekvira Gas Godown",
    "address_line3": "B/H Sports Complex",
    "city": "Bhayander-East",
    "state": "Maharashtra",
    "pin_code": "401105",
    "country": "INDIA",
    "telephone": "+91(0) 22 28191035",
    "email": "info@nirmalprecision.com",
    "gst_number": "27AACCN3516F2ZP",
    "iec_number": "",
    "supplier_ac_no": "",
    "default_currency": "USD",
    "default_country_of_origin": "INDIA",
    "default_payment_terms": "",
    "default_delivery_terms": "",
    "default_lut_arn": "",
    "signature_name": "",
    "signature_designation": "",
}


# ============================================================================
# NUMBER / FORMAT HELPERS
# ============================================================================

_UNITS = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
    "Eighty", "Ninety",
]


def _two_digit_words(n):
    if n < 20:
        return _UNITS[n]
    return (_TENS[n // 10] + (" " + _UNITS[n % 10] if n % 10 else "")).strip()


def _three_digit_words(n):
    if n < 100:
        return _two_digit_words(n)
    remainder = n % 100
    text = _UNITS[n // 100] + " Hundred"
    if remainder:
        text += " " + _two_digit_words(remainder)
    return text


def _integer_to_words(number):
    """Convert a non-negative integer to English words (Indian numbering)."""
    number = int(number)
    if number == 0:
        return "Zero"

    parts = []
    # Indian system: crore, lakh, thousand, hundred
    for divisor, label in (
        (10000000, "Crore"),
        (100000, "Lakh"),
        (1000, "Thousand"),
    ):
        if number >= divisor:
            chunk = number // divisor
            number %= divisor
            parts.append(f"{_integer_to_words(chunk)} {label}")
    if number >= 100:
        parts.append(_three_digit_words(number))
        number = 0
    elif number > 0:
        parts.append(_two_digit_words(number))

    return " ".join(p for p in parts if p).strip()


def amount_in_words(amount, currency):
    """
    Build an amount-in-words string using the supplied currency.

    Example (USD): Two Thousand Two Hundred Sixty One Dollars and Fifty Three
    Cents Only.
    """
    currency = (currency or "").upper().strip()
    major_s, major_p, minor_s, minor_p = CURRENCY_WORDS.get(
        currency, (currency or "Units", (currency or "Units"), "Cent", "Cents")
    )

    try:
        value = round(float(amount or 0), 2)
    except (TypeError, ValueError):
        value = 0.0

    negative = value < 0
    value = abs(value)

    whole = int(value)
    # Convert fractional part from the rounded value to avoid float artefacts.
    fraction = int(round((value - whole) * 100))
    if fraction == 100:
        whole += 1
        fraction = 0

    major_word = major_s if whole == 1 else major_p
    minor_word = minor_s if fraction == 1 else minor_p

    words = f"{_integer_to_words(whole)} {major_word}"
    if fraction:
        words += f" and {_integer_to_words(fraction)} {minor_word}"
    else:
        words += " and No Cents" if currency != "INR" else " and No Paise"

    if negative:
        words = "Minus " + words
    return words + " Only"


def invoice_to_calculated_amount(quantity, rate_per_100):
    """Amount = Quantity / 100 x Rate per 100 Pcs."""
    try:
        qty = float(quantity or 0)
    except (TypeError, ValueError):
        qty = 0.0
    try:
        rate = float(rate_per_100 or 0)
    except (TypeError, ValueError):
        rate = 0.0
    return round(qty / 100.0 * rate, 2)


def _to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _clean(value):
    """Normalise a submitted text value to a trimmed string or None."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _is_numeric(value):
    try:
        float(str(value).replace(",", "").strip())
        return True
    except (TypeError, ValueError):
        return False


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (TypeError, ValueError):
            continue
    return None


def format_amount(value, decimals=2):
    """Format a numeric amount with thousands separators and fixed decimals."""
    try:
        return f"{float(value or 0):,.{decimals}f}"
    except (TypeError, ValueError):
        return "0.00"


# ============================================================================
# BLUEPRINT / MODEL FACTORY
# ============================================================================

def create_invoice_blueprint(db, crm_models=None):
    """Build the invoice blueprint bound to the application's SQLAlchemy db.

    ``crm_models`` is an optional mapping used only for the CRM import
    endpoints, e.g. ``{"customer": Quote, "product": Product}``. Kept as a
    parameter so this module never has to import the application module.
    """
    crm_models = crm_models or {}
    CrmCustomer = crm_models.get("customer")
    CrmOrder = crm_models.get("order")
    CrmProduct = crm_models.get("product")

    # ------------------------------------------------------------------
    # MODELS
    # ------------------------------------------------------------------
    class Invoice(db.Model):
        __tablename__ = "invoices"
        __table_args__ = (
            db.UniqueConstraint(
                "invoice_number", "revision", name="uq_invoice_number_revision"
            ),
        )

        id = db.Column(db.Integer, primary_key=True)
        invoice_number = db.Column(db.String(100), nullable=False, index=True)
        revision = db.Column(db.Integer, default=1)
        parent_invoice_id = db.Column(db.Integer, nullable=True)
        revision_of = db.Column(db.String(100), nullable=True)
        is_latest = db.Column(db.Boolean, default=True)

        invoice_date = db.Column(db.Date)

        # Invoice information
        currency = db.Column(db.String(10), default="USD")
        supplier_ac_no = db.Column(db.String(100))
        country_of_origin = db.Column(db.String(100))
        country_of_final_destination = db.Column(db.String(100))

        # Orders
        customer_order_no = db.Column(db.String(100))
        internal_order_no = db.Column(db.String(100))

        # Export / HS information
        hs_code = db.Column(db.String(100))
        claim_duty_drawback = db.Column(db.Boolean, default=False)
        duty_drawback_statement = db.Column(db.Text)
        additional_export_declaration = db.Column(db.Text)
        lut_arn_no = db.Column(db.String(100))
        remarks = db.Column(db.Text)

        # Totals
        calculated_total = db.Column(db.Float, default=0.0)
        manual_total_override = db.Column(db.Boolean, default=False)
        manual_total_value = db.Column(db.Float, nullable=True)
        total = db.Column(db.Float, default=0.0)
        amount_in_words = db.Column(db.Text)

        # Signature
        signature_name = db.Column(db.String(200))
        signature_date = db.Column(db.Date)
        signature_designation = db.Column(db.String(200))
        signature_image = db.Column(db.String(500))

        # Status / lifecycle
        status = db.Column(db.String(20), default="Draft")
        generated_at = db.Column(db.DateTime)
        pdf_path = db.Column(db.String(500))
        source_crm_customer_id = db.Column(db.Integer, nullable=True)
        source_crm_order_id = db.Column(db.Integer, nullable=True)

        created_by = db.Column(db.String(100), default="admin")
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(
            db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

        items = db.relationship(
            "InvoiceItem",
            backref="invoice",
            cascade="all, delete-orphan",
            order_by="InvoiceItem.sort_order",
            foreign_keys="InvoiceItem.invoice_id",
        )
        exporter = db.relationship(
            "InvoiceExporterDetails",
            backref="invoice",
            uselist=False,
            cascade="all, delete-orphan",
        )
        consignee = db.relationship(
            "InvoiceConsigneeDetails",
            backref="invoice",
            uselist=False,
            cascade="all, delete-orphan",
        )
        shipping = db.relationship(
            "InvoiceShippingDetails",
            backref="invoice",
            uselist=False,
            cascade="all, delete-orphan",
        )

        @property
        def display_total(self):
            if self.manual_total_override and self.manual_total_value is not None:
                return round(float(self.manual_total_value), 2)
            return round(calc_items_total(self.items), 2)

        @property
        def total_display(self):
            return format_amount(self.display_total)

    class InvoiceItem(db.Model):
        __tablename__ = "invoice_items"

        id = db.Column(db.Integer, primary_key=True)
        invoice_id = db.Column(
            db.Integer, db.ForeignKey("invoices.id", ondelete="CASCADE")
        )
        item_no = db.Column(db.String(50))
        order_no = db.Column(db.String(100))
        no_of_packages = db.Column(db.String(50))
        package_type = db.Column(db.String(100))
        description = db.Column(db.Text)
        quantity = db.Column(db.Float, default=0.0)
        rate_per_100 = db.Column(db.Float, default=0.0)
        currency = db.Column(db.String(10))
        amount = db.Column(db.Float, default=0.0)
        manual_amount_override = db.Column(db.Boolean, default=False)
        hs_code = db.Column(db.String(100))
        duty_drawback_info = db.Column(db.Text)
        sort_order = db.Column(db.Integer, default=0)

    class InvoiceExporterDetails(db.Model):
        __tablename__ = "invoice_exporter_details"

        id = db.Column(db.Integer, primary_key=True)
        invoice_id = db.Column(
            db.Integer, db.ForeignKey("invoices.id", ondelete="CASCADE")
        )
        exporter_name = db.Column(db.String(255))
        address_line1 = db.Column(db.String(255))
        address_line2 = db.Column(db.String(255))
        address_line3 = db.Column(db.String(255))
        city = db.Column(db.String(100))
        state = db.Column(db.String(100))
        pin_code = db.Column(db.String(50))
        country = db.Column(db.String(100))
        telephone = db.Column(db.String(100))
        email = db.Column(db.String(200))
        gst_number = db.Column(db.String(100))
        iec_number = db.Column(db.String(100))
        supplier_ac_no = db.Column(db.String(100))

    class InvoiceConsigneeDetails(db.Model):
        __tablename__ = "invoice_consignee_details"

        id = db.Column(db.Integer, primary_key=True)
        invoice_id = db.Column(
            db.Integer, db.ForeignKey("invoices.id", ondelete="CASCADE")
        )
        consignee_name = db.Column(db.String(255))
        company_name = db.Column(db.String(255))
        address_line1 = db.Column(db.String(255))
        address_line2 = db.Column(db.String(255))
        address_line3 = db.Column(db.String(255))
        city = db.Column(db.String(100))
        state = db.Column(db.String(100))
        postal_code = db.Column(db.String(50))
        country = db.Column(db.String(100))
        phone = db.Column(db.String(100))
        email = db.Column(db.String(200))
        customer_order_no = db.Column(db.String(100))
        internal_order_no = db.Column(db.String(100))

    class InvoiceShippingDetails(db.Model):
        __tablename__ = "invoice_shipping_details"

        id = db.Column(db.Integer, primary_key=True)
        invoice_id = db.Column(
            db.Integer, db.ForeignKey("invoices.id", ondelete="CASCADE")
        )
        terms_of_delivery = db.Column(db.String(255))
        payment_terms = db.Column(db.String(255))
        pre_carriage_by = db.Column(db.String(255))
        place_of_receipt = db.Column(db.String(255))
        by_pre_carrier = db.Column(db.String(255))
        port_of_loading = db.Column(db.String(255))
        port_of_discharge = db.Column(db.String(255))
        final_destination = db.Column(db.String(255))
        vessel_flight_no = db.Column(db.String(255))

    class InvoiceDefaults(db.Model):
        __tablename__ = "invoice_defaults"

        id = db.Column(db.Integer, primary_key=True)
        exporter_name = db.Column(db.String(255))
        address_line1 = db.Column(db.String(255))
        address_line2 = db.Column(db.String(255))
        address_line3 = db.Column(db.String(255))
        city = db.Column(db.String(100))
        state = db.Column(db.String(100))
        pin_code = db.Column(db.String(50))
        country = db.Column(db.String(100))
        telephone = db.Column(db.String(100))
        email = db.Column(db.String(200))
        gst_number = db.Column(db.String(100))
        iec_number = db.Column(db.String(100))
        supplier_ac_no = db.Column(db.String(100))
        default_currency = db.Column(db.String(10), default="USD")
        default_country_of_origin = db.Column(db.String(100))
        default_payment_terms = db.Column(db.String(255))
        default_delivery_terms = db.Column(db.String(255))
        default_lut_arn = db.Column(db.String(100))
        signature_name = db.Column(db.String(200))
        signature_designation = db.Column(db.String(200))
        signature_image = db.Column(db.String(500))
        updated_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_by = db.Column(db.String(100))

    class InvoiceHistory(db.Model):
        __tablename__ = "invoice_history"

        id = db.Column(db.Integer, primary_key=True)
        invoice_id = db.Column(db.Integer, index=True)
        invoice_number = db.Column(db.String(100))
        revision = db.Column(db.Integer, default=1)
        action = db.Column(db.String(50))
        snapshot = db.Column(db.Text)
        note = db.Column(db.String(500))
        created_by = db.Column(db.String(100))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ------------------------------------------------------------------
    # SERIALISATION / SNAPSHOT HELPERS
    # ------------------------------------------------------------------
    def _iso(d):
        return d.isoformat() if isinstance(d, (date, datetime)) else None

    def snapshot_invoice(invoice):
        """Return a JSON-serialisable snapshot of every field on the invoice."""
        return {
            "invoice": {
                "invoice_number": invoice.invoice_number,
                "revision": invoice.revision,
                "invoice_date": _iso(invoice.invoice_date),
                "currency": invoice.currency,
                "supplier_ac_no": invoice.supplier_ac_no,
                "country_of_origin": invoice.country_of_origin,
                "country_of_final_destination": invoice.country_of_final_destination,
                "customer_order_no": invoice.customer_order_no,
                "internal_order_no": invoice.internal_order_no,
                "hs_code": invoice.hs_code,
                "claim_duty_drawback": bool(invoice.claim_duty_drawback),
                "duty_drawback_statement": invoice.duty_drawback_statement,
                "additional_export_declaration": invoice.additional_export_declaration,
                "lut_arn_no": invoice.lut_arn_no,
                "remarks": invoice.remarks,
                "calculated_total": invoice.calculated_total,
                "manual_total_override": bool(invoice.manual_total_override),
                "manual_total_value": invoice.manual_total_value,
                "total": invoice.display_total,
                "amount_in_words": invoice.amount_in_words,
                "signature_name": invoice.signature_name,
                "signature_date": _iso(invoice.signature_date),
                "signature_designation": invoice.signature_designation,
                "signature_image": invoice.signature_image,
                "status": invoice.status,
            },
            "exporter": _row_dict(
                invoice.exporter,
                [
                    "exporter_name", "address_line1", "address_line2",
                    "address_line3", "city", "state", "pin_code", "country",
                    "telephone", "email", "gst_number", "iec_number",
                    "supplier_ac_no",
                ],
            ),
            "consignee": _row_dict(
                invoice.consignee,
                [
                    "consignee_name", "company_name", "address_line1",
                    "address_line2", "address_line3", "city", "state",
                    "postal_code", "country", "phone", "email",
                    "customer_order_no", "internal_order_no",
                ],
            ),
            "shipping": _row_dict(
                invoice.shipping,
                [
                    "terms_of_delivery", "payment_terms", "pre_carriage_by",
                    "place_of_receipt", "by_pre_carrier", "port_of_loading",
                    "port_of_discharge", "final_destination", "vessel_flight_no",
                ],
            ),
            "items": [
                {
                    "item_no": it.item_no,
                    "order_no": it.order_no,
                    "no_of_packages": it.no_of_packages,
                    "package_type": it.package_type,
                    "description": it.description,
                    "quantity": it.quantity,
                    "rate_per_100": it.rate_per_100,
                    "currency": it.currency,
                    "amount": it.amount,
                    "manual_amount_override": bool(it.manual_amount_override),
                    "hs_code": it.hs_code,
                    "duty_drawback_info": it.duty_drawback_info,
                    "sort_order": it.sort_order,
                }
                for it in sorted(invoice.items, key=lambda i: i.sort_order or 0)
            ],
        }

    def _row_dict(row, fields):
        if row is None:
            return {}
        return {f: getattr(row, f) for f in fields}

    def record_history(invoice, action, note=None):
        entry = InvoiceHistory(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            revision=invoice.revision,
            action=action,
            snapshot=json.dumps(snapshot_invoice(invoice), default=str),
            note=note,
            created_by=session.get("admin_user", "admin"),
        )
        db.session.add(entry)

    def calc_items_total(items):
        total = 0.0
        for it in items or []:
            total += float(it.amount or 0)
        return round(total, 2)

    # ------------------------------------------------------------------
    # ACCESS CONTROL
    # ------------------------------------------------------------------
    def require_admin():
        """Return a redirect response if the caller is not logged in."""
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return None

    def ensure_invoice_tables():
        """Create invoice tables if they do not exist yet (checkfirst=True)."""
        for model in (
            Invoice,
            InvoiceItem,
            InvoiceExporterDetails,
            InvoiceConsigneeDetails,
            InvoiceShippingDetails,
            InvoiceDefaults,
            InvoiceHistory,
        ):
            try:
                model.__table__.create(db.engine, checkfirst=True)
            except Exception:
                db.session.rollback()

    def get_defaults():
        """Fetch or lazily create the singleton company-defaults row."""
        defaults = InvoiceDefaults.query.first()
        if defaults is None:
            defaults = InvoiceDefaults(**NIRMAL_DEFAULTS)
            db.session.add(defaults)
            db.session.commit()
        return defaults

    def next_invoice_number():
        """Suggest the next sequential invoice number (NIR<year><seq>)."""
        year = datetime.utcnow().year
        prefix = f"NIR{year}"
        rows = (
            Invoice.query.filter(Invoice.invoice_number.like(f"{prefix}%"))
            .with_entities(Invoice.invoice_number)
            .all()
        )
        max_seq = 0
        for (num,) in rows:
            tail = (num or "")[len(prefix):]
            if tail.isdigit():
                max_seq = max(max_seq, int(tail))
        return f"{prefix}{max_seq + 1:03d}"

    # ------------------------------------------------------------------
    # FORM (DE)HYDRATION
    # ------------------------------------------------------------------
    TEXT_FIELDS_INVOICE = [
        "invoice_date", "currency", "supplier_ac_no", "country_of_origin",
        "country_of_final_destination", "customer_order_no", "internal_order_no",
        "hs_code", "duty_drawback_statement", "additional_export_declaration",
        "lut_arn_no", "remarks", "amount_in_words", "signature_name",
        "signature_date", "signature_designation",
    ]

    EXPORTER_FIELDS = [
        "exporter_name", "address_line1", "address_line2", "address_line3",
        "city", "state", "pin_code", "country", "telephone", "email",
        "gst_number", "iec_number", "supplier_ac_no",
    ]

    CONSIGNEE_FIELDS = [
        "consignee_name", "company_name", "address_line1", "address_line2",
        "address_line3", "city", "state", "postal_code", "country", "phone",
        "email", "customer_order_no", "internal_order_no",
    ]

    SHIPPING_FIELDS = [
        "terms_of_delivery", "payment_terms", "pre_carriage_by",
        "place_of_receipt", "by_pre_carrier", "port_of_loading",
        "port_of_discharge", "final_destination", "vessel_flight_no",
    ]

    def collect_invoice_payload(form, existing=None):
        """Read all submitted invoice fields into a plain dict (no persistence)."""
        payload = {
            "invoice_number": _clean(form.get("invoice_number")),
            "invoice_date": _parse_date(form.get("invoice_date")),
            "currency": _clean(form.get("currency")) or "USD",
            "supplier_ac_no": _clean(form.get("supplier_ac_no")),
            "country_of_origin": _clean(form.get("country_of_origin")),
            "country_of_final_destination": _clean(
                form.get("country_of_final_destination")
            ),
            "customer_order_no": _clean(form.get("customer_order_no")),
            "internal_order_no": _clean(form.get("internal_order_no")),
            "hs_code": _clean(form.get("hs_code")),
            "claim_duty_drawback": form.get("claim_duty_drawback") in ("on", "true", "1", "yes"),
            "duty_drawback_statement": _clean(form.get("duty_drawback_statement")),
            "additional_export_declaration": _clean(
                form.get("additional_export_declaration")
            ),
            "lut_arn_no": _clean(form.get("lut_arn_no")),
            "remarks": _clean(form.get("remarks")),
            "manual_total_override": form.get("manual_total_override") in ("on", "true", "1", "yes"),
            "signature_name": _clean(form.get("signature_name")),
            "signature_date": _parse_date(form.get("signature_date")),
            "signature_designation": _clean(form.get("signature_designation")),
        }
        payload["manual_total_value"] = (
            _to_float(form.get("manual_total_value")) if payload["manual_total_override"] else None
        )
        payload["amount_in_words"] = _clean(form.get("amount_in_words"))
        payload["signature_image"] = _clean(form.get("signature_image"))
        payload["source_crm_customer_id"] = _to_int(form.get("source_crm_customer_id"), None)
        payload["source_crm_order_id"] = _to_int(form.get("source_crm_order_id"), None)
        payload["exporter"] = {f: _clean(form.get(f"exporter_{f}")) for f in EXPORTER_FIELDS}
        payload["consignee"] = {f: _clean(form.get(f"consignee_{f}")) for f in CONSIGNEE_FIELDS}
        payload["shipping"] = {f: _clean(form.get(f"shipping_{f}")) for f in SHIPPING_FIELDS}
        payload["items"] = collect_items(form)
        return payload

    def collect_items(form):
        """Read the dynamic item rows from the form."""
        item_numbers = form.getlist("item_item_no[]")
        order_nos = form.getlist("item_order_no[]")
        packages = form.getlist("item_no_of_packages[]")
        package_types = form.getlist("item_package_type[]")
        descriptions = form.getlist("item_description[]")
        quantities = form.getlist("item_quantity[]")
        rates = form.getlist("item_rate_per_100[]")
        currencies = form.getlist("item_currency[]")
        amounts = form.getlist("item_amount[]")
        override_flags = form.getlist("item_manual_amount_override[]")
        hs_codes = form.getlist("item_hs_code[]")
        drawbacks = form.getlist("item_duty_drawback_info[]")

        items = []
        row_count = len(descriptions)
        for i in range(row_count):
            def g(lst):
                return lst[i] if i < len(lst) else ""

            raw_qty = (g(quantities) or "").strip()
            raw_rate = (g(rates) or "").strip()
            qty = _to_float(raw_qty)
            rate = _to_float(raw_rate)
            override = g(override_flags) in ("on", "true", "1", "yes")
            amount = _to_float(g(amounts)) if override else invoice_to_calculated_amount(qty, rate)
            items.append(
                {
                    "item_no": _clean(g(item_numbers)),
                    "order_no": _clean(g(order_nos)),
                    "no_of_packages": _clean(g(packages)),
                    "package_type": _clean(g(package_types)),
                    "description": _clean(g(descriptions)),
                    "quantity": qty,
                    "rate_per_100": rate,
                    "currency": _clean(g(currencies)),
                    "amount": amount,
                    "manual_amount_override": override,
                    "hs_code": _clean(g(hs_codes)),
                    "duty_drawback_info": _clean(g(drawbacks)),
                    "sort_order": i,
                    "_raw_quantity": raw_qty,
                    "_raw_rate": raw_rate,
                }
            )
        return items

    def validate_payload(payload, invoice_id=None, revision=1):
        """Return a list of human readable validation errors."""
        errors = []

        if not payload.get("invoice_number"):
            errors.append("Invoice number is required.")
        else:
            clash = Invoice.query.filter(
                Invoice.invoice_number == payload["invoice_number"],
                Invoice.revision == revision,
                Invoice.id != invoice_id,
            ).first()
            if clash:
                errors.append(
                    f"Invoice number '{payload['invoice_number']}' already exists "
                    f"(revision {revision}). Please use a different number."
                )

        if not payload.get("currency"):
            errors.append("Currency is required.")
        if not payload.get("invoice_date"):
            errors.append("Invoice date is required.")

        consignee = payload.get("consignee") or {}
        if not (consignee.get("consignee_name") or consignee.get("company_name")):
            errors.append("Consignee name is required.")

        exporter = payload.get("exporter") or {}
        if not exporter.get("exporter_name"):
            errors.append("Exporter name is required.")

        items = payload.get("items") or []
        real_items = [it for it in items if (it.get("description") or it.get("quantity") or it.get("amount"))]
        if not real_items:
            errors.append("At least one invoice item is required.")
        else:
            for idx, it in enumerate(items, start=1):
                if not (it.get("description") or it.get("quantity") or it.get("amount")):
                    continue
                if it.get("_raw_quantity") and not _is_numeric(it["_raw_quantity"]):
                    errors.append(f"Item {idx}: Quantity must be numeric.")
                if it.get("_raw_rate") and not _is_numeric(it["_raw_rate"]):
                    errors.append(f"Item {idx}: Rate must be numeric.")
                if not it.get("description"):
                    errors.append(f"Item {idx}: Description of goods is required.")

        if payload.get("manual_total_override") and payload.get("manual_total_value") is None:
            errors.append("Manual total override is enabled but no total value was entered.")

        return errors

    def apply_payload(invoice, payload):
        """Copy the collected payload onto the invoice and its child rows."""
        invoice.invoice_number = payload["invoice_number"]
        invoice.invoice_date = payload["invoice_date"]
        invoice.currency = payload["currency"]
        invoice.supplier_ac_no = payload["supplier_ac_no"]
        invoice.country_of_origin = payload["country_of_origin"]
        invoice.country_of_final_destination = payload["country_of_final_destination"]
        invoice.customer_order_no = payload["customer_order_no"]
        invoice.internal_order_no = payload["internal_order_no"]
        invoice.hs_code = payload["hs_code"]
        invoice.claim_duty_drawback = payload["claim_duty_drawback"]
        invoice.duty_drawback_statement = payload["duty_drawback_statement"]
        invoice.additional_export_declaration = payload["additional_export_declaration"]
        invoice.lut_arn_no = payload["lut_arn_no"]
        invoice.remarks = payload["remarks"]
        invoice.manual_total_override = payload["manual_total_override"]
        invoice.manual_total_value = payload["manual_total_value"]
        invoice.signature_name = payload["signature_name"]
        invoice.signature_date = payload["signature_date"]
        invoice.signature_designation = payload["signature_designation"]
        invoice.signature_image = payload.get("signature_image")
        invoice.source_crm_customer_id = payload.get("source_crm_customer_id")
        invoice.source_crm_order_id = payload.get("source_crm_order_id")

        # Items (replace wholesale - rows are fully described by the form)
        item_columns = {
            "item_no", "order_no", "no_of_packages", "package_type",
            "description", "quantity", "rate_per_100", "currency", "amount",
            "manual_amount_override", "hs_code", "duty_drawback_info",
        }
        invoice.items.clear()
        db.session.flush()
        for idx, item in enumerate(payload["items"]):
            clean = {k: v for k, v in item.items() if k in item_columns}
            invoice.items.append(InvoiceItem(sort_order=idx, **clean))
        db.session.flush()

        calculated = calc_items_total(invoice.items)
        invoice.calculated_total = calculated
        invoice.total = invoice.display_total

        # Manual amount-in-words wins; otherwise derive it from total + currency.
        invoice.amount_in_words = (
            payload.get("amount_in_words")
            or amount_in_words(invoice.total, invoice.currency)
        )

        # Child rows
        def upsert(attr, model, values):
            row = getattr(invoice, attr)
            if row is None:
                row = model(invoice_id=invoice.id)
                setattr(invoice, attr, row)
            for key, value in values.items():
                setattr(row, key, value)

        upsert("exporter", InvoiceExporterDetails, payload["exporter"])
        upsert("consignee", InvoiceConsigneeDetails, payload["consignee"])
        upsert("shipping", InvoiceShippingDetails, payload["shipping"])
        invoice.updated_at = datetime.utcnow()

    def clone_invoice(source, new_number=None, as_revision=False):
        """Deep-copy an invoice into a new Draft row (duplicate or revision)."""
        clone = Invoice(
            invoice_number=new_number or source.invoice_number,
            revision=(source.revision + 1) if as_revision else 1,
            parent_invoice_id=source.id,
            revision_of=source.invoice_number,
            is_latest=True,
            invoice_date=source.invoice_date,
            currency=source.currency,
            supplier_ac_no=source.supplier_ac_no,
            country_of_origin=source.country_of_origin,
            country_of_final_destination=source.country_of_final_destination,
            customer_order_no=source.customer_order_no,
            internal_order_no=source.internal_order_no,
            hs_code=source.hs_code,
            claim_duty_drawback=source.claim_duty_drawback,
            duty_drawback_statement=source.duty_drawback_statement,
            additional_export_declaration=source.additional_export_declaration,
            lut_arn_no=source.lut_arn_no,
            remarks=source.remarks,
            manual_total_override=source.manual_total_override,
            manual_total_value=source.manual_total_value,
            amount_in_words=source.amount_in_words,
            signature_name=source.signature_name,
            signature_date=source.signature_date,
            signature_designation=source.signature_designation,
            signature_image=source.signature_image,
            status="Draft",
            source_crm_customer_id=source.source_crm_customer_id,
            source_crm_order_id=source.source_crm_order_id,
            created_by=session.get("admin_user", "admin"),
        )
        db.session.add(clone)
        db.session.flush()

        for it in sorted(source.items, key=lambda r: r.sort_order or 0):
            clone.items.append(
                InvoiceItem(
                    item_no=it.item_no,
                    order_no=it.order_no,
                    no_of_packages=it.no_of_packages,
                    package_type=it.package_type,
                    description=it.description,
                    quantity=it.quantity,
                    rate_per_100=it.rate_per_100,
                    currency=it.currency,
                    amount=it.amount,
                    manual_amount_override=it.manual_amount_override,
                    hs_code=it.hs_code,
                    duty_drawback_info=it.duty_drawback_info,
                    sort_order=it.sort_order,
                )
            )

        if source.exporter:
            clone.exporter = InvoiceExporterDetails(
                **{f: getattr(source.exporter, f) for f in EXPORTER_FIELDS}
            )
        if source.consignee:
            clone.consignee = InvoiceConsigneeDetails(
                **{f: getattr(source.consignee, f) for f in CONSIGNEE_FIELDS}
            )
        if source.shipping:
            clone.shipping = InvoiceShippingDetails(
                **{f: getattr(source.shipping, f) for f in SHIPPING_FIELDS}
            )

        clone.calculated_total = calc_items_total(clone.items)
        clone.total = clone.display_total
        return clone

    # ------------------------------------------------------------------
    # RENDERING CONTEXT
    # ------------------------------------------------------------------
    def build_render_context(invoice):
        """Assemble the flat context consumed by the PDF/preview template."""
        exp = invoice.exporter
        con = invoice.consignee
        shp = invoice.shipping
        items = sorted(invoice.items, key=lambda i: i.sort_order or 0)

        exporter_lines = []
        if exp:
            if exp.address_line1:
                exporter_lines.append(exp.address_line1)
            if exp.address_line2:
                exporter_lines.append(exp.address_line2)
            if exp.address_line3:
                exporter_lines.append(exp.address_line3)
            city_line = ", ".join(
                p for p in [exp.city, exp.state, exp.pin_code] if p
            )
            if city_line:
                exporter_lines.append(city_line)

        consignee_lines = []
        if con:
            if con.address_line1:
                consignee_lines.append(con.address_line1)
            if con.address_line2:
                consignee_lines.append(con.address_line2)
            if con.address_line3:
                consignee_lines.append(con.address_line3)
            city_line = ", ".join(
                p for p in [con.city, con.state, con.postal_code] if p
            )
            if city_line:
                consignee_lines.append(city_line)

        return {
            "invoice": invoice,
            "exporter": exp,
            "consignee": con,
            "shipping": shp,
            "items": items,
            "exporter_lines": exporter_lines,
            "consignee_lines": consignee_lines,
            "invoice_date_str": (
                invoice.invoice_date.strftime("%d/%m/%Y")
                if invoice.invoice_date
                else ""
            ),
            "signature_date_str": (
                invoice.signature_date.strftime("%d/%m/%Y")
                if invoice.signature_date
                else ""
            ),
            "total_display": format_amount(invoice.display_total),
            "amount_words": invoice.amount_in_words or amount_in_words(
                invoice.display_total, invoice.currency
            ),
            "signature_image_url": (
                url_for("static", filename=invoice.signature_image)
                if invoice.signature_image
                else None
            ),
            "signature_image_path": (
                os.path.join(current_app.static_folder, invoice.signature_image)
                if invoice.signature_image
                else None
            ),
        }

    # ------------------------------------------------------------------
    # BLUEPRINT ROUTES
    # ------------------------------------------------------------------
    bp = Blueprint("invoices", __name__, url_prefix="/admin/invoices")

    @bp.app_template_filter("amt")
    def _amt(value, decimals=2):
        """Format a number for the invoice design (thousands separators)."""
        if value in (None, ""):
            return ""
        return format_amount(value, decimals)

    @bp.before_request
    def _guard():
        if not session.get("admin"):
            return redirect(url_for("admin_login"))

    @bp.route("/")
    def invoice_list():
        ensure_invoice_tables()
        q = (request.args.get("q") or "").strip()
        customer = (request.args.get("customer") or "").strip()
        order_no = (request.args.get("order_no") or "").strip()
        status = (request.args.get("status") or "").strip()
        date_from = _parse_date(request.args.get("date_from"))
        date_to = _parse_date(request.args.get("date_to"))

        query = Invoice.query
        if q:
            query = query.filter(Invoice.invoice_number.ilike(f"%{q}%"))
        if status:
            query = query.filter(Invoice.status == status)
        if order_no:
            query = query.filter(
                db.or_(
                    Invoice.customer_order_no.ilike(f"%{order_no}%"),
                    Invoice.internal_order_no.ilike(f"%{order_no}%"),
                )
            )
        if date_from:
            query = query.filter(Invoice.invoice_date >= date_from)
        if date_to:
            query = query.filter(Invoice.invoice_date <= date_to)

        invoices = query.order_by(
            Invoice.created_at.desc(), Invoice.revision.desc()
        ).all()

        if customer:
            needle = customer.lower()
            invoices = [
                inv
                for inv in invoices
                if inv.consignee
                and needle
                in " ".join(
                    p
                    for p in [
                        inv.consignee.consignee_name,
                        inv.consignee.company_name,
                    ]
                    if p
                ).lower()
            ]

        return render_template(
            "admin_invoices.html",
            invoices=invoices,
            q=q,
            customer=customer,
            order_no=order_no,
            status=status,
            date_from=request.args.get("date_from", ""),
            date_to=request.args.get("date_to", ""),
            statuses=INVOICE_STATUSES,
        )

    @bp.route("/new", methods=["GET", "POST"])
    def invoice_new():
        ensure_invoice_tables()
        defaults = get_defaults()

        if request.method == "POST":
            payload = collect_invoice_payload(request.form)
            errors = validate_payload(payload, revision=1)
            if errors:
                for err in errors:
                    flash(err, "error")
                return render_template(
                    "admin_invoice_form.html",
                    invoice=None,
                    payload=payload,
                    defaults=defaults,
                    currencies=CURRENCIES,
                    suggested_number=payload.get("invoice_number") or next_invoice_number(),
                    mode="create",
                )

            invoice = Invoice(
                invoice_number=payload["invoice_number"],
                revision=1,
                is_latest=True,
                status="Draft",
                created_by=session.get("admin_user", "admin"),
            )
            db.session.add(invoice)
            db.session.flush()
            apply_payload(invoice, payload)
            record_history(invoice, "created", "Invoice created as draft")
            db.session.commit()

            flash("Invoice saved as draft.", "success")
            if request.form.get("action") == "generate":
                return redirect(url_for("invoices.invoice_generate", invoice_id=invoice.id))
            return redirect(url_for("invoices.invoice_edit", invoice_id=invoice.id))

        # GET -> pre-filled blank invoice from company defaults
        suggested_number = next_invoice_number()
        payload = {
            "invoice_number": suggested_number,
            "invoice_date": date.today().isoformat(),
            "currency": defaults.default_currency or "USD",
            "supplier_ac_no": defaults.supplier_ac_no,
            "country_of_origin": defaults.default_country_of_origin or "INDIA",
            "country_of_final_destination": None,
            "customer_order_no": None,
            "internal_order_no": None,
            "hs_code": None,
            "claim_duty_drawback": False,
            "duty_drawback_statement": None,
            "additional_export_declaration": None,
            "lut_arn_no": defaults.default_lut_arn,
            "remarks": None,
            "manual_total_override": False,
            "manual_total_value": None,
            "amount_in_words": None,
            "signature_name": defaults.signature_name,
            "signature_date": date.today().isoformat(),
            "signature_designation": defaults.signature_designation,
            "signature_image": defaults.signature_image,
            "exporter": {
                f: getattr(defaults, f, None) for f in EXPORTER_FIELDS
            },
            "consignee": {f: None for f in CONSIGNEE_FIELDS},
            "shipping": {f: None for f in SHIPPING_FIELDS},
            "items": [],
        }
        return render_template(
            "admin_invoice_form.html",
            invoice=None,
            payload=payload,
            defaults=defaults,
            currencies=CURRENCIES,
            suggested_number=suggested_number,
            mode="create",
        )

    @bp.route("/<int:invoice_id>/edit", methods=["GET", "POST"])
    def invoice_edit(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        defaults = get_defaults()

        if request.method == "POST":
            payload = collect_invoice_payload(request.form)
            errors = validate_payload(payload, invoice_id=invoice.id, revision=invoice.revision)
            if errors:
                for err in errors:
                    flash(err, "error")
                return render_template(
                    "admin_invoice_form.html",
                    invoice=invoice,
                    payload=payload,
                    defaults=defaults,
                    currencies=CURRENCIES,
                    suggested_number=payload.get("invoice_number"),
                    mode="edit",
                )

            was_issued = invoice.status == "Generated"
            if was_issued:
                # Preserve the issued document: snapshot it, then create a new
                # revision that carries the edits. The original is never altered.
                record_history(invoice, "revised", "Issued invoice superseded by revision")
                invoice.is_latest = False
                db.session.flush()
                revised = clone_invoice(invoice, as_revision=True)
                next_rev = (
                    db.session.query(db.func.max(Invoice.revision))
                    .filter(Invoice.invoice_number == invoice.invoice_number)
                    .scalar()
                    or invoice.revision
                ) + 1
                revised.revision = next_rev
                apply_payload(revised, payload)
                revised.status = "Draft"
                record_history(revised, "created", "Revision created from issued invoice")
                db.session.commit()
                flash(
                    "Issued invoice preserved as revision "
                    f"{invoice.revision}. Your edits were saved as revision "
                    f"{revised.revision} (Draft).",
                    "success",
                )
                return redirect(url_for("invoices.invoice_edit", invoice_id=revised.id))

            apply_payload(invoice, payload)
            record_history(invoice, "updated", "Draft invoice updated")
            db.session.commit()
            flash("Invoice updated.", "success")
            if request.form.get("action") == "generate":
                return redirect(url_for("invoices.invoice_generate", invoice_id=invoice.id))
            return redirect(url_for("invoices.invoice_edit", invoice_id=invoice.id))

        payload = hydrate_payload(invoice)
        return render_template(
            "admin_invoice_form.html",
            invoice=invoice,
            payload=payload,
            defaults=defaults,
            currencies=CURRENCIES,
            suggested_number=invoice.invoice_number,
            mode="edit",
        )

    def hydrate_payload(invoice):
        return {
            "invoice_number": invoice.invoice_number,
            "invoice_date": _iso(invoice.invoice_date),
            "currency": invoice.currency,
            "supplier_ac_no": invoice.supplier_ac_no,
            "country_of_origin": invoice.country_of_origin,
            "country_of_final_destination": invoice.country_of_final_destination,
            "customer_order_no": invoice.customer_order_no,
            "internal_order_no": invoice.internal_order_no,
            "hs_code": invoice.hs_code,
            "claim_duty_drawback": bool(invoice.claim_duty_drawback),
            "duty_drawback_statement": invoice.duty_drawback_statement,
            "additional_export_declaration": invoice.additional_export_declaration,
            "lut_arn_no": invoice.lut_arn_no,
            "remarks": invoice.remarks,
            "manual_total_override": bool(invoice.manual_total_override),
            "manual_total_value": invoice.manual_total_value,
            "amount_in_words": invoice.amount_in_words,
            "signature_name": invoice.signature_name,
            "signature_date": _iso(invoice.signature_date),
            "signature_designation": invoice.signature_designation,
            "signature_image": invoice.signature_image,
            "source_crm_customer_id": invoice.source_crm_customer_id,
            "source_crm_order_id": invoice.source_crm_order_id,
            "exporter": _row_dict(invoice.exporter, EXPORTER_FIELDS),
            "consignee": _row_dict(invoice.consignee, CONSIGNEE_FIELDS),
            "shipping": _row_dict(invoice.shipping, SHIPPING_FIELDS),
            "items": [
                {
                    "item_no": it.item_no,
                    "order_no": it.order_no,
                    "no_of_packages": it.no_of_packages,
                    "package_type": it.package_type,
                    "description": it.description,
                    "quantity": it.quantity,
                    "rate_per_100": it.rate_per_100,
                    "currency": it.currency,
                    "amount": it.amount,
                    "manual_amount_override": bool(it.manual_amount_override),
                    "hs_code": it.hs_code,
                    "duty_drawback_info": it.duty_drawback_info,
                }
                for it in sorted(invoice.items, key=lambda i: i.sort_order or 0)
            ],
        }

    @bp.route("/<int:invoice_id>")
    def invoice_view(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        history = (
            InvoiceHistory.query.filter_by(invoice_id=invoice.id)
            .order_by(InvoiceHistory.created_at.desc())
            .all()
        )
        return render_template(
            "admin_invoice_view.html", invoice=invoice, history=history
        )

    @bp.route("/<int:invoice_id>/preview")
    def invoice_preview(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        return render_template("admin_invoice_preview.html", invoice=invoice)

    @bp.route("/<int:invoice_id>/preview-frame")
    def invoice_preview_frame(invoice_id):
        """Raw HTML of the invoice design - same template as the PDF."""
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        ctx = build_render_context(invoice)
        return render_template("invoice_pdf.html", **ctx)

    @bp.route("/<int:invoice_id>/generate", methods=["POST", "GET"])
    def invoice_generate(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)

        payload = hydrate_payload(invoice)
        errors = validate_payload(payload, invoice_id=invoice.id, revision=invoice.revision)
        if errors:
            for err in errors:
                flash(err, "error")
            return redirect(url_for("invoices.invoice_edit", invoice_id=invoice.id))

        invoice.calculated_total = calc_items_total(invoice.items)
        invoice.total = invoice.display_total
        if not invoice.amount_in_words:
            invoice.amount_in_words = amount_in_words(invoice.total, invoice.currency)
        invoice.status = "Generated"
        invoice.generated_at = datetime.utcnow()

        # Snapshot every invoice field at issue time so later changes to company
        # defaults or CRM data can never alter this issued document.
        record_history(invoice, "generated", "Invoice generated / issued")
        db.session.commit()

        flash("Invoice generated.", "success")
        return redirect(url_for("invoices.invoice_pdf", invoice_id=invoice.id))

    @bp.route("/<int:invoice_id>/pdf")
    def invoice_pdf(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        ctx = build_render_context(invoice)
        html = render_template("invoice_pdf.html", **ctx)

        try:
            from xhtml2pdf import pisa
        except ImportError:
            abort(500, description=(
                "PDF generation library 'xhtml2pdf' is not installed. "
                "Run: pip install xhtml2pdf"
            ))

        pdf_io = io.BytesIO()
        # link_callback lets xhtml2pdf resolve relative static paths (e.g. the
        # signature image) to files on disk.
        def link_callback(uri, rel):
            if uri.startswith("http://") or uri.startswith("https://"):
                return uri
            if uri.startswith("/static/"):
                return os.path.join(current_app.static_folder, uri[len("/static/"):])
            return uri

        result = pisa.CreatePDF(
            html, dest=pdf_io, encoding="utf-8", link_callback=link_callback
        )
        if result.err:
            abort(500, description="Failed to render invoice PDF.")

        pdf_io.seek(0)

        # Deterministic filename: INVOICE_NUMBER.pdf (revisions get a suffix so
        # the original issue is never overwritten).
        filename = invoice.invoice_number or f"invoice-{invoice.id}"
        if invoice.revision and invoice.revision > 1:
            filename = f"{filename}_R{invoice.revision}"
        filename = secure_filename(filename) + ".pdf"

        rel_path = os.path.join("invoices", filename)
        abs_dir = os.path.join(current_app.static_folder, "invoices")
        os.makedirs(abs_dir, exist_ok=True)
        with open(os.path.join(abs_dir, filename), "wb") as fh:
            fh.write(pdf_io.getvalue())
        invoice.pdf_path = rel_path
        db.session.commit()
        pdf_io.seek(0)

        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    @bp.route("/<int:invoice_id>/duplicate", methods=["POST"])
    def invoice_duplicate(invoice_id):
        ensure_invoice_tables()
        source = Invoice.query.get_or_404(invoice_id)

        # The invoice number must never be duplicated: allocate a fresh one.
        new_number = next_invoice_number()
        while Invoice.query.filter_by(invoice_number=new_number, revision=1).first():
            new_number = _increment_number(new_number)

        clone = clone_invoice(source, new_number=new_number)
        clone.status = "Draft"
        clone.generated_at = None
        db.session.flush()
        record_history(clone, "duplicated", f"Duplicated from {source.invoice_number}")
        db.session.commit()

        flash(
            f"Invoice duplicated as {clone.invoice_number}. Update the invoice "
            "number before generating.",
            "success",
        )
        return redirect(url_for("invoices.invoice_edit", invoice_id=clone.id))

    def _increment_number(number):
        import re as _re
        m = _re.match(r"^(.*?)(\d+)$", number or "")
        if m:
            return f"{m.group(1)}{int(m.group(2)) + 1:0{len(m.group(2))}d}"
        return f"{number}-COPY"

    @bp.route("/<int:invoice_id>/delete", methods=["POST"])
    def invoice_delete(invoice_id):
        ensure_invoice_tables()
        invoice = Invoice.query.get_or_404(invoice_id)
        number = invoice.invoice_number
        db.session.delete(invoice)
        db.session.commit()
        flash(f"Invoice {number} deleted.", "success")
        return redirect(url_for("invoices.invoice_list"))

    # ---------------------- COMPANY DEFAULTS ----------------------
    @bp.route("/defaults", methods=["GET", "POST"])
    def invoice_defaults():
        ensure_invoice_tables()
        defaults = get_defaults()

        if request.method == "POST":
            for f in EXPORTER_FIELDS + [
                "default_currency", "default_country_of_origin",
                "default_payment_terms", "default_delivery_terms",
                "default_lut_arn", "signature_name", "signature_designation",
            ]:
                value = _clean(request.form.get(f))
                if f == "default_currency" and not value:
                    value = "USD"
                setattr(defaults, f, value)
            defaults.updated_at = datetime.utcnow()
            defaults.updated_by = session.get("admin_user", "admin")
            db.session.commit()
            flash(
                "Company defaults saved. Existing invoices are unchanged.",
                "success",
            )
            return redirect(url_for("invoices.invoice_defaults"))

        return render_template(
            "admin_invoice_defaults.html",
            defaults=defaults,
            currencies=CURRENCIES,
        )

    # ---------------------- SIGNATURE UPLOAD ----------------------
    @bp.route("/upload_signature", methods=["POST"])
    def upload_signature():
        file = request.files.get("signature_file")
        if not file or not file.filename:
            return jsonify({"ok": False, "error": "No file supplied"}), 400
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in SIGNATURE_EXTENSIONS:
            return jsonify({"ok": False, "error": "Unsupported image type"}), 400
        filename = secure_filename(file.filename)
        filename = f"signature_{int(datetime.utcnow().timestamp())}_{filename}"
        rel_dir = os.path.join("img", "signatures")
        abs_dir = os.path.join(current_app.static_folder, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        file.save(os.path.join(abs_dir, filename))
        return jsonify({"ok": True, "path": os.path.join(rel_dir, filename)})

    # ---------------------- CRM MAPPING ----------------------
    @bp.route("/api/crm/customers")
    def crm_customers():
        """Search CRM customer records for consignee import."""
        term = (request.args.get("q") or "").strip()
        results = []
        if CrmCustomer is not None:
            query = CrmCustomer.query
            if term:
                query = query.filter(
                    db.or_(
                        CrmCustomer.company.ilike(f"%{term}%"),
                        CrmCustomer.name.ilike(f"%{term}%"),
                        CrmCustomer.email.ilike(f"%{term}%"),
                    )
                )
            for row in query.order_by(CrmCustomer.id.desc()).limit(25).all():
                results.append(
                    {
                        "id": row.id,
                        "name": getattr(row, "name", None),
                        "company": getattr(row, "company", None),
                        "email": getattr(row, "email", None),
                        "phone": getattr(row, "phone", None),
                        "country": getattr(row, "country", None),
                        "message": getattr(row, "message", None),
                    }
                )
        return jsonify(results)

    @bp.route("/api/crm/orders")
    def crm_orders():
        """Search CRM order records (quotes act as orders in this schema)."""
        term = (request.args.get("q") or "").strip()
        results = []
        source = CrmOrder or CrmCustomer
        if source is not None:
            query = source.query
            if request.args.get("customer_id"):
                query = query.filter(source.id == _to_int(request.args.get("customer_id")))
            if term:
                query = query.filter(
                    db.or_(
                        source.company.ilike(f"%{term}%"),
                        source.name.ilike(f"%{term}%"),
                    )
                )
            for row in query.order_by(source.id.desc()).limit(25).all():
                results.append(
                    {
                        "id": row.id,
                        "order_no": f"ORD-{row.id:05d}",
                        "company": getattr(row, "company", None),
                        "customer": getattr(row, "name", None),
                        "country": getattr(row, "country", None),
                    }
                )
        return jsonify(results)

    @bp.route("/api/crm/products")
    def crm_products():
        """Search CRM products for invoice item import."""
        term = (request.args.get("q") or "").strip()
        results = []
        if CrmProduct is not None:
            query = CrmProduct.query
            if hasattr(CrmProduct, "status"):
                query = query.filter(CrmProduct.status == "active")
            if term:
                query = query.filter(CrmProduct.name.ilike(f"%{term}%"))
            for row in query.limit(25).all():
                results.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "code": getattr(row, "code", None),
                        "standard": getattr(row, "standard", None),
                        "material": getattr(row, "material", None),
                    }
                )
        return jsonify(results)

    return bp
