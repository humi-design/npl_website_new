import os 
import time
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import pymysql
from urllib.parse import quote_plus, quote
from werkzeug.utils import secure_filename
import uuid
import logging

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pymysql.install_as_MySQLdb()

app = Flask(__name__)

# ======================
# MYSQL CONFIG
# ======================

DB_USER = "humijxhw_nirmal_web"
DB_PASS = quote_plus("Ralpana@1808")
DB_NAME = "humijxhw_nirmal_web"
DB_HOST = "localhost"

app.config["SQLALCHEMY_DATABASE_URI"] = \
f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.secret_key = "supersecretkey"

# ======================
# FILE UPLOAD CONFIG
# ======================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'step', 'dwg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ======================
# HELPER FUNCTIONS
# ======================

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def generate_meta_content(product):
    """Generate SEO meta title, description, and content for a product"""
    # Generate meta title
    standard = product.din_standard or product.iso_standard or product.astm_standard or ''
    if standard:
        meta_title = f"{standard} {product.name} Manufacturer | Nirmal Precision"
    else:
        meta_title = f"{product.name} Manufacturer | Nirmal Precision"
    
    # Generate meta description
    material = product.material or ''
    meta_desc = f"{product.name} - {product.short_description or 'Precision engineered'}. "
    meta_desc += f"{material} material. "
    if product.din_standard:
        meta_desc += f"Complies with {product.din_standard}. "
    meta_desc += f"ISO 9001:2015 certified. Global export to 80+ countries. Request quote."
    
    return meta_title, meta_desc

def generate_product_content(product):
    """Generate comprehensive product page content"""
    standard = product.din_standard or product.iso_standard or product.astm_standard or 'Custom'
    
    # Introduction
    intro = f"The {product.name} is a precision-engineered component designed for demanding industrial applications. "
    intro += f"Manufactured by Nirmal Precision with over 25 years of expertise, this product meets international quality standards "
    intro += f"and is trusted by engineers and procurement professionals worldwide."
    
    # Key Features
    features = []
    if product.material:
        features.append(f"Premium {product.material} construction for durability and corrosion resistance")
    if product.din_standard:
        features.append(f"Compliant with {product.din_standard} German industrial standards")
    if product.iso_standard:
        features.append(f"Meets {product.iso_standard} international specifications")
    if product.astm_standard:
        features.append(f"Conforms to {product.astm_standard} American standards")
    features.append("Precision manufacturing with tight tolerances")
    features.append("100% quality inspection before dispatch")
    features.append("Complete documentation and traceability")
    
    # Applications
    applications = product.applications.split('\n') if product.applications else []
    
    # Industries
    industries = product.industries.split('\n') if product.industries else []
    
    return {
        'intro': intro,
        'features': features,
        'applications': [a.strip() for a in applications if a.strip()],
        'industries': [i.strip() for i in industries if i.strip()],
        'standard': standard
    }

# ======================
# MODELS
# ======================

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    name = db.Column(db.String(200))
    
    # URL Slug
    slug = db.Column(db.String(255), unique=True, nullable=False)
    
    # Standards
    din_standard = db.Column(db.String(50))
    iso_standard = db.Column(db.String(50))
    astm_standard = db.Column(db.String(50))
    
    # Categorization
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))
    
    # Descriptions
    short_description = db.Column(db.String(500))
    long_description = db.Column(db.Text)
    
    # Content
    applications = db.Column(db.Text)
    industries = db.Column(db.Text)
    materials = db.Column(db.Text)
    surface_finish = db.Column(db.Text)
    available_sizes = db.Column(db.Text)
    thread_types = db.Column(db.Text)
    manufacturing_process = db.Column(db.Text)
    tolerance = db.Column(db.String(100))
    quality_standards = db.Column(db.Text)
    technical_specifications = db.Column(db.Text)
    
    # Specs
    material = db.Column(db.String(100))
    size = db.Column(db.String(100))
    standard = db.Column(db.String(100))
    
    # SEO Fields
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    keywords = db.Column(db.Text)
    canonical_url = db.Column(db.String(500))
    og_title = db.Column(db.String(255))
    og_description = db.Column(db.Text)
    twitter_title = db.Column(db.String(255))
    twitter_description = db.Column(db.Text)
    
    # Media
    image = db.Column(db.String(500))
    images = db.Column(db.Text)  # JSON string of multiple images
    downloads = db.Column(db.Text)  # JSON string of download links
    
    # Status
    status = db.Column(db.String(20), default='active')
    featured = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_related_products(self):
        """Get related products based on category and material"""
        return Product.query.filter(
            Product.category == self.category,
            Product.id != self.id,
            Product.status == 'active'
        ).limit(8).all()
    
    def get_slug(self):
        """Generate URL slug"""
        if self.slug:
            return self.slug
        standard = self.din_standard or self.iso_standard or ''
        name = self.name.lower().replace(' ', '-')
        if standard:
            return f"{standard.lower().replace(' ', '-')}-{name}"
        return name


class ProductCategory(db.Model):
    __tablename__ = "product_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    image = db.Column(db.String(500))
    order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Material(db.Model):
    __tablename__ = "materials"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    properties = db.Column(db.Text)
    applications = db.Column(db.Text)
    advantages = db.Column(db.Text)
    industries = db.Column(db.Text)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    image = db.Column(db.String(500))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Industry(db.Model):
    __tablename__ = "industries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    applications = db.Column(db.Text)
    products = db.Column(db.Text)  # Related product keywords
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    image = db.Column(db.String(500))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    slug = db.Column(db.String(255), unique=True)
    content = db.Column(db.Text)
    excerpt = db.Column(db.String(500))
    category = db.Column(db.String(100))
    tags = db.Column(db.String(255))
    image = db.Column(db.String(500))
    author = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)


class ProductFAQ(db.Model):
    __tablename__ = "product_faqs"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    question = db.Column(db.String(500))
    answer = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProductRelated(db.Model):
    __tablename__ = "product_related"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    related_id = db.Column(db.Integer, db.ForeignKey('products.id'))


class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))
    product_id = db.Column(db.Integer)
    qty = db.Column(db.Integer)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Quote(db.Model):
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    company = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    country = db.Column(db.String(100))
    message = db.Column(db.Text)


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    company = db.Column(db.String(200))
    country = db.Column(db.String(100))
    message = db.Column(db.Text)


class Compare(db.Model):
    __tablename__ = "compare"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)


class Country(db.Model):
    __tablename__ = "countries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(100), unique=True)


class ExportStat(db.Model):
    __tablename__ = "export_stats"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    value = db.Column(db.String(50))

class QuoteItem(db.Model):
    __tablename__ = "quote_items"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    qty = db.Column(db.Integer)

@app.before_request
def ensure_session_id():
    """Ensure every visitor has a unique session ID and DB is ready."""
    # Initialize database table if needed
    ensure_db_ready()
    
    # Ensure session ID exists
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        logger.debug(f"Created new session_id: {session['user_id']}")


@app.context_processor
def inject_cart_context():
    """
    Inject user-specific cart data into all templates.
    
    - If user is logged in, fetches cart using user_id from session
    - If user is not logged in, fetches cart using session_id from session
    - NEVER uses global Cart.query.all() which would show all users' carts
    """
    try:
        # Skip context for static files
        from flask import request
        if request.endpoint and request.endpoint.startswith('static'):
            return dict(cart=[], cart_count=0, categories=[], compare=[])
        
        current_session_id = session.get("user_id")
        
        # Safety check: if no session_id, return empty cart
        if not current_session_id:
            return dict(cart=[], cart_count=0, categories=[], compare=[])
        
        # Fetch only THIS visitor's cart items
        user_cart = Cart.query.filter_by(session_id=current_session_id).all()
        cart_count = len(user_cart)
        
        # Debug logging
        logger.debug(f"[CART CONTEXT] session_id: {current_session_id}, cart_count: {cart_count}")
        
        return dict(
            cart=user_cart,
            cart_count=cart_count,
            categories=Category.query.all(),
            compare=Compare.query.all()
        )
    except Exception as e:
        logger.error(f"Cart context error: {e}")
        return dict(cart=[], cart_count=0, categories=[], compare=[])


# ======================
# HOME
# ======================

@app.route("/")
def home():
    categories = Category.query.all()

    industries = [
        "Oil & Gas", "Construction", "Automobile", "Railway",
        "Energy", "Infrastructure", "Marine", "Aerospace"
    ]

    # Load all images from static/products
    product_folder = os.path.join(app.static_folder, "img", "products")

    images = [
        img for img in os.listdir(product_folder)
        if img.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    ]

    images.sort()

    return render_template(
        "index.html",
        industries=industries,
        categories=categories,
        images=images
    )


# ======================
# ABOUT
# ======================

@app.route("/about")
def about():
    return render_template("about.html")


# ======================
# PRODUCTS
# ======================

@app.route("/products")
def products_page():
    category = request.args.get("category")
    search = request.args.get("search")

    query = Product.query

    if category:
        query = query.filter(Product.category == category)

    if search:
        query = query.filter(Product.name.contains(search))

    products = query.all()
    categories = Category.query.all()

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        selected_category=category,
        search_text=search
    )


# ======================
# CART
# ======================

@app.route("/add/<int:id>")
def add_to_cart(id):
    user_id = session.get("user_id")

    existing = Cart.query.filter_by(
        product_id=id,
        session_id=user_id
    ).first()

    if existing:
        existing.qty += 1
    else:
        item = Cart(product_id=id, qty=1, session_id=user_id)
        db.session.add(item)

    db.session.commit()
    return redirect(request.referrer or url_for("products_page"))


@app.route("/cart")
def cart():
    user_id = session.get("user_id")

    cart_items = Cart.query.filter_by(session_id=user_id).all()

    enriched_cart = []

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            enriched_cart.append({
                "id": item.id,
                "name": product.name,
                "image": product.image,
                "qty": item.qty,
                "spec": product.standard
            })

    return render_template("cart.html", cart=enriched_cart)


@app.route("/remove/<int:id>")
def remove_from_cart(id):
    user_id = session.get("user_id")

    item = Cart.query.filter_by(id=id, session_id=user_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()

    return ("", 204)


@app.route("/update_qty/<int:id>/<action>")
def update_qty(id, action):
    user_id = session.get("user_id")

    item = Cart.query.filter_by(id=id, session_id=user_id).first()

    if not item:
        return ("", 404)

    if action == "increase":
        item.qty += 1
    elif action == "decrease":
        item.qty -= 1
        if item.qty <= 0:
            db.session.delete(item)
            db.session.commit()
            return ("deleted", 200)

    db.session.commit()
    return {"qty": item.qty}
    
    
@app.route("/set_qty/<int:id>", methods=["POST"])
def set_qty(id):
    try:
        user_id = session.get("user_id")
        
        # Filter by BOTH id AND session_id for security
        item = Cart.query.filter_by(id=id, session_id=user_id).first()

        if not item:
            return ("not found", 404)

        qty = int(request.form.get("qty"))

        if qty <= 0:
            db.session.delete(item)
            db.session.commit()
            return ("deleted", 200)

        item.qty = qty
        db.session.commit()

        return {"qty": item.qty}

    except Exception as e:
        print("ERROR:", e)
        return ("error", 500)



# ======================
# COMPARE
# ======================

@app.route("/compare_add/<int:id>")
def compare_add(id):
    if Compare.query.count() >= 4:
        return redirect(url_for("compare"))

    item = Compare(product_id=id)
    db.session.add(item)
    db.session.commit()

    return redirect(url_for("compare"))

@app.route("/remove_compare/<int:id>")
def remove_compare(id):
    item = Compare.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for("compare"))

@app.route("/clear_compare")
def clear_compare():
    Compare.query.delete()
    db.session.commit()
    return redirect(url_for("compare"))


@app.route("/compare")
def compare():
    compare_items = Compare.query.all()

    products = []

    for item in compare_items:
        p = Product.query.get(item.product_id)

        if p:
            # ✅ Inject dynamic specs dictionary
            p.specs = {
                "Material": p.material or "—",
                "Size": p.size or "—",
                "Standard": p.standard or "—",
                "Category": p.category or "—"
            }

            # 👉 Optional future-ready fields (safe fallback)
            p.specs["Strength Grade"] = getattr(p, "strength", "—") or "—"
            p.specs["Surface Coating"] = getattr(p, "coating", "—") or "—"

            products.append(p)

    # ✅ Build dynamic spec keys (VERY IMPORTANT)
    spec_keys = set()
    for p in products:
        spec_keys.update(p.specs.keys())

    spec_keys = sorted(spec_keys)

    return render_template(
        "compare.html",
        compare=products,
        spec_keys=spec_keys
    )


# ======================
# SUBMIT QUOTE
# ======================

from email.mime.text import MIMEText
import smtplib

@app.route("/submit_quote", methods=["POST"])
def submit_quote():
    try:
        # =========================
        # GET FORM DATA
        # =========================
        name = request.form.get("name")
        email = request.form.get("email")
        company = request.form.get("company")
        phone = request.form.get("phone")
        country = request.form.get("country")
        message = request.form.get("message")

        # =========================
        # CREATE QUOTE
        # =========================
        q = Quote(
            name=name,
            email=email,
            company=company,
            phone=phone,
            country=country,
            message=message
        )

        db.session.add(q)
        db.session.commit()   # ⚠️ required to get q.id

        # =========================
        # GET CART ITEMS (SAFE)
        # =========================
        user_id = session.get("user_id")

        cart_items = []
        if user_id:
            cart_items = Cart.query.filter_by(session_id=user_id).all()

        # =========================
        # SAVE CART ITEMS TO QUOTE
        # =========================
        email_items_text = ""

        for item in cart_items:
            qi = QuoteItem(
                quote_id=q.id,
                product_id=item.product_id,
                qty=item.qty
            )
            db.session.add(qi)

            # Build email content
            product = Product.query.get(item.product_id)
            if product:
                email_items_text += f"{product.name} (Qty: {item.qty})\n"

        # =========================
        # CLEAR CART
        # =========================
        if user_id:
            Cart.query.filter_by(session_id=user_id).delete()

        db.session.commit()

        # =========================
        # SEND EMAIL
        # =========================
        full_message = f"""
New RFQ Received

Name: {name}
Email: {email}
Company: {company}
Phone: {phone}
Country: {country}

Items:
{email_items_text}

Message:
{message}
"""

        msg = MIMEText(full_message)
        msg["Subject"] = f"New RFQ from {name}"
        msg["From"] = email
        msg["To"] = "yourcompany@email.com"  # 🔁 change this

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login("yourcompany@email.com", "your_app_password")
            server.send_message(msg)
            server.quit()
        except Exception as mail_error:
            print("EMAIL ERROR:", mail_error)

        # =========================
        # SUCCESS
        # =========================
        return redirect(url_for("cart", success=1))

    except Exception as e:
        print("ERROR:", e)
        return f"Internal Server Error: {e}"

# ======================
# EXPORT
# ======================

@app.route("/export")
def export():
    countries = Country.query.all()

    # ✅ Hardcoded stats (safe, no DB dependency)
    stats = [
        {"title": "Countries Exported", "value": "80+"},
        {"title": "Years Experience", "value": "25+"},
        {"title": "Global Clients", "value": "2000+"},
        {"title": "Products", "value": "50K+"}
    ]

    return render_template(
        "export.html",
        countries=countries,
        stats=stats
    )


# ======================
# CONTACT
# ======================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            c = Contact(
                name=request.form["name"],
                email=request.form["email"],
                company=request.form["company"],
                country=request.form["country"],
                message=request.form["message"]
            )
            db.session.add(c)
            db.session.commit()

            flash("Message sent successfully!")
            return redirect(url_for("contact"))

        except Exception as e:
            print(e)
            flash("Error sending message")

    return render_template(
        "contact.html",
        categories=Category.query.all(),
        company_address="A-12, Priya Industrial Estate, Behind Mira Bhayandar Sports, Mumbai,401105, India",
        company_phone="+91 8424849942",
        company_email="sales@nirmalprecision.com",
        business_hours="Mon–Sat: 9:00 AM – 6:00 PM IST",
        map_title="Mumbai Manufacturing Unit"
    )
    



# ======================
# ADMIN
# ======================

# ======================
# ADMIN CONFIG
# ======================

# ======================
# ADMIN LOGIN
# ======================

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USER and
            request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect(url_for("admin"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ======================
# ADMIN DASHBOARD
# ======================

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    return render_template(
        "admin.html",
        products=Product.query.all(),
        categories=Category.query.all(),
        countries=Country.query.all(),
        stats=[]
    )


# ======================
# PRODUCT CRUD
# ======================

@app.route('/admin/upload_image', methods=['POST'])
def upload_image():
    """Handle AJAX image upload for inline editing"""
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        upload_path = os.path.join(app.root_path, 'static', 'img', 'products', filename)
        file.save(upload_path)
        return f'/static/img/products/{filename}'
    return 'Invalid file type', 400


@app.route("/admin/add_product", methods=["POST"])
def add_product():
    image_path = request.form.get("image") or ""
    
    # Handle file upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_path = os.path.join(app.root_path, 'static', 'img', 'products', filename)
            file.save(upload_path)
            image_path = f'/static/img/products/{filename}'
    
    p = Product(
        code=request.form["code"],
        name=request.form["name"],
        category=request.form["category"],
        material=request.form.get("material"),
        size=request.form.get("size"),
        standard=request.form.get("standard"),
        image=image_path
    )
    db.session.add(p)
    db.session.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete_product/<int:id>")
def delete_product(id):
    p = Product.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for("admin"))


# ======================
# CATEGORY
# ======================

@app.route("/admin/add_category", methods=["POST"])
def add_category():
    db.session.add(Category(name=request.form["name"]))
    db.session.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete_category/<int:id>")
def delete_category(id):
    c = Category.query.get(id)
    if c:
        db.session.delete(c)
        db.session.commit()
    return redirect(url_for("admin"))


# ======================
# COUNTRY
# ======================

@app.route("/admin/add_country", methods=["POST"])
def add_country():
    db.session.add(Country(name=request.form["name"]))
    db.session.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete_country/<int:id>")
def delete_country(id):
    c = Country.query.get(id)
    if c:
        db.session.delete(c)
        db.session.commit()
    return redirect(url_for("admin"))


# ======================
# EXPORT STATS
# ======================

@app.route("/admin/add_stat", methods=["POST"])
def add_stat():
    db.session.add(
        ExportStat(
            title=request.form["title"],
            value=request.form["value"]
        )
    )
    db.session.commit()
    return redirect(url_for("admin"))
    
@app.route("/admin/update_product/<int:id>", methods=["POST"])
def update_product(id):
    p = Product.query.get(id)

    if p:
        p.code = request.form["code"]
        p.name = request.form["name"]
        p.category = request.form["category"]
        p.material = request.form.get("material")
        p.size = request.form.get("size")
        p.standard = request.form.get("standard")
        
        # Handle file upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_path = os.path.join(app.root_path, 'static', 'img', 'products', filename)
                file.save(upload_path)
                p.image = f'/static/img/products/{filename}'
        elif request.form.get("image"):
            p.image = request.form.get("image")

        db.session.commit()

    return redirect(url_for("admin"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")


# ======================
# DATABASE INITIALIZATION
# ======================

_cart_table_initialized = False

def init_cart_table():
    """Ensure session_id column exists in Cart table."""
    global _cart_table_initialized
    if _cart_table_initialized:
        return
        
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('carts')]
        
        if 'session_id' not in columns:
            logger.info("Adding session_id column to carts table...")
            db.session.execute(db.text('ALTER TABLE carts ADD COLUMN session_id VARCHAR(100)'))
            db.session.commit()
            logger.info("session_id column added successfully")
        
        _cart_table_initialized = True
    except Exception as e:
        logger.warning(f"Could not initialize cart table: {e}")
        try:
            db.session.rollback()
        except:
            pass

def ensure_db_ready():
    """Call this on first request to initialize DB if needed."""
    try:
        init_cart_table()
    except:
        pass

# ======================

# ======================
# SITEMAP
# ======================

@app.route("/sitemap.xml")
def sitemap():
    """Generate XML sitemap for search engines"""
    from flask import Response
    
    categories = Category.query.all()
    products = Product.query.all()
    
    # Static pages
    static_pages = [
        {"loc": "https://nirmalprecision.com/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "https://nirmalprecision.com/about", "priority": "0.8", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/products", "priority": "0.9", "changefreq": "daily"},
        {"loc": "https://nirmalprecision.com/export", "priority": "0.8", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/contact", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/privacy", "priority": "0.3", "changefreq": "yearly"},
        {"loc": "https://nirmalprecision.com/terms", "priority": "0.3", "changefreq": "yearly"},
    ]
    
    # Category pages
    category_pages = []
    for cat in categories:
        category_pages.append({
            "loc": f"https://nirmalprecision.com/products?category={cat.name.replace(' ', '+')}",
            "priority": "0.8",
            "changefreq": "weekly"
        })
    
    # Product pages (using query parameters for now)
    product_pages = []
    for product in products:
        product_pages.append({
            "loc": f"https://nirmalprecision.com/products?search={product.code}",
            "priority": "0.7",
            "changefreq": "weekly"
        })
    
    # Country pages
    country_pages = [
        {"loc": "https://nirmalprecision.com/country/usa", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/germany", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/uk", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/france", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/italy", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/spain", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/netherlands", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/sweden", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/canada", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/australia", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/country/uae", "priority": "0.7", "changefreq": "monthly"},
    ]
    
    xml_sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
'''
    
    for page in static_pages:
        xml_sitemap += f'''    <url>
        <loc>{page["loc"]}</loc>
        <priority>{page["priority"]}</priority>
        <changefreq>{page["changefreq"]}</changefreq>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    </url>
'''
    
    for page in category_pages:
        xml_sitemap += f'''    <url>
        <loc>{page["loc"]}</loc>
        <priority>{page["priority"]}</priority>
        <changefreq>{page["changefreq"]}</changefreq>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    </url>
'''
    
    for page in product_pages:
        xml_sitemap += f'''    <url>
        <loc>{page["loc"]}</loc>
        <priority>{page["priority"]}</priority>
        <changefreq>{page["changefreq"]}</changefreq>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    </url>
'''
    
    for page in country_pages:
        xml_sitemap += f'''    <url>
        <loc>{page["loc"]}</loc>
        <priority>{page["priority"]}</priority>
        <changefreq>{page["changefreq"]}</changefreq>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    </url>
'''
    
    xml_sitemap += '</urlset>'
    
    return Response(xml_sitemap, mimetype='application/xml')


# ======================
# ROBOTS.TXT
# ======================

@app.route("/robots.txt")
def robots():
    """Generate robots.txt for search engines"""
    from flask import Response
    
    robots_txt = '''# Robots.txt for Nirmal Precision
# https://nirmalprecision.com

User-agent: *
Allow: /

# Sitemap locations
Sitemap: https://nirmalprecision.com/sitemap.xml
Sitemap: https://nirmalprecision.com/sitemap-dynamic.xml

# Crawl-delay for polite crawling
Crawl-delay: 1

# Allow important bots
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: Baiduspider
Allow: /

User-agent: YandexBot
Allow: /

# AI Bots
User-agent: GPTBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: CCBot
Allow: /

# Block admin areas
Disallow: /admin/
Disallow: /admin/login
'''
    
    return Response(robots_txt, mimetype='text/plain')


# ======================
# COUNTRY PAGES
# ======================

@app.route("/country/<country_code>")
def country_page(country_code):
    """Generate country-specific landing pages"""
    country_data = {
        "usa": {
            "name": "United States",
            "flag": "🇺🇸",
            "standards": ["ASTM", "ASME", "SAE", "ANSI", "ISO"],
            "industries": ["Automotive", "Aerospace", "Medical Devices", "Electronics", "Construction"],
            "description": "Nirmal Precision exports precision components and industrial fasteners to the United States, serving major OEMs and distributors across all 50 states."
        },
        "germany": {
            "name": "Germany",
            "flag": "🇩🇪",
            "standards": ["DIN", "ISO", "EN", "VDMA"],
            "industries": ["Automotive", "Industrial Machinery", "Renewable Energy", "Medical Technology"],
            "description": "As a DIN standards specialist, we supply precision components to German automotive, machinery, and industrial manufacturers with full European compliance."
        },
        "uk": {
            "name": "United Kingdom",
            "flag": "🇬🇧",
            "standards": ["BS", "ISO", "DIN", "EN"],
            "industries": ["Aerospace", "Automotive", "Railway", "Defense"],
            "description": "We supply precision fasteners and components to UK aerospace, automotive, and defense contractors meeting British Standards and EU compliance."
        },
        "france": {
            "name": "France",
            "flag": "🇫🇷",
            "standards": ["NF", "DIN", "ISO", "EN"],
            "industries": ["Aerospace", "Automotive", "Nuclear", "Luxury Goods Manufacturing"],
            "description": "Our precision components serve French aerospace, automotive, and nuclear industries with NF and DIN compliant products."
        },
        "italy": {
            "name": "Italy",
            "flag": "🇮🇹",
            "standards": ["UNI", "DIN", "ISO", "EN"],
            "industries": ["Automotive", "Industrial Equipment", "Fashion Machinery", "Food Processing"],
            "description": "We supply precision fasteners and components to Italian manufacturers across automotive, industrial equipment, and food processing sectors."
        },
        "spain": {
            "name": "Spain",
            "flag": "🇪🇸",
            "standards": ["UNE", "DIN", "ISO", "EN"],
            "industries": ["Automotive", "Renewable Energy", "Aerospace", "Railway"],
            "description": "Our Spanish partners rely on our precision components for automotive, renewable energy, and aerospace applications."
        },
        "netherlands": {
            "name": "Netherlands",
            "flag": "🇳🇱",
            "standards": ["NEN", "DIN", "ISO", "EN"],
            "industries": ["Semiconductor", "Industrial Machinery", "Chemical Processing", "Agriculture"],
            "description": "We serve Dutch high-tech industries including semiconductor manufacturing, industrial machinery, and chemical processing."
        },
        "sweden": {
            "name": "Sweden",
            "flag": "🇸🇪",
            "standards": ["SIS", "DIN", "ISO", "EN"],
            "industries": ["Automotive", "Heavy Industry", "Telecom", "Medical Devices"],
            "description": "Swedish automotive and heavy industry manufacturers trust our precision components for demanding applications."
        },
        "canada": {
            "name": "Canada",
            "flag": "🇨🇦",
            "standards": ["CSA", "ASTM", "ASME", "DIN", "ISO"],
            "industries": ["Mining", "Oil & Gas", "Automotive", "Aerospace"],
            "description": "We supply precision fasteners and components to Canadian mining, oil & gas, and manufacturing industries."
        },
        "australia": {
            "name": "Australia",
            "flag": "🇦🇺",
            "standards": ["AS", "ASTM", "DIN", "ISO"],
            "industries": ["Mining", "Agriculture", "Automotive", "Construction"],
            "description": "Australian mining, agriculture, and manufacturing sectors rely on our precision components for critical applications."
        },
        "uae": {
            "name": "United Arab Emirates",
            "flag": "🇦🇪",
            "standards": ["ESMA", "DIN", "ISO", "ASTM"],
            "industries": ["Oil & Gas", "Construction", "Marine", "Renewable Energy"],
            "description": "We serve UAE's oil & gas, construction, and marine industries with precision components meeting international standards."
        }
    }
    
    if country_code not in country_data:
        return redirect(url_for('home'))
    
    data = country_data[country_code]
    
    return render_template(
        'country.html',
        country=data,
        country_code=country_code
    )


# ======================
# BLOG SECTION
# ======================

@app.route("/blog")
def blog():
    """Blog listing page"""
    return render_template('blog.html')


@app.route("/blog/<slug>")
def blog_post(slug):
    """Individual blog post page"""
    return render_template('blog_post.html', slug=slug)


# ======================
# LANDING PAGES
# ======================

@app.route("/fastener-manufacturer-india")
def fastener_manufacturer():
    """Landing page for fastener manufacturer India"""
    return render_template('landing/fastener_manufacturer.html')


@app.route("/bolt-manufacturer-india")
def bolt_manufacturer():
    """Landing page for bolt manufacturer India"""
    return render_template('landing/bolt_manufacturer.html')


@app.route("/precision-machined-parts")
def precision_machined():
    """Landing page for precision machined parts"""
    return render_template('landing/precision_machined.html')


@app.route("/cnc-machined-parts-manufacturer")
def cnc_machined():
    """Landing page for CNC machined parts"""
    return render_template('landing/cnc_machined.html')


# ======================
# PRODUCT PAGES (SEO-FRIENDLY URLS)
# ======================

@app.route("/products/<slug>")
def product_page(slug):
    """Individual product page with SEO-friendly URL"""
    product = Product.query.filter_by(slug=slug, status='active').first()
    
    if not product:
        abort(404)
    
    # Get related products
    related_products = product.get_related_products()
    
    # Get FAQs for this product
    faqs = ProductFAQ.query.filter_by(product_id=product.id).order_by(ProductFAQ.order).all()
    
    # Generate meta content if not set
    if not product.meta_title:
        product.meta_title = f"{product.din_standard or product.iso_standard or ''} {product.name} | Nirmal Precision"
    if not product.meta_description:
        product.meta_description = f"{product.name} - {product.short_description or 'Precision engineered component'}. "
        if product.material:
            product.meta_description += f"{product.material} material. "
        if product.din_standard:
            product.meta_description += f"Complies with {product.din_standard}. "
        product.meta_description += "ISO 9001:2015 certified. Global export available."
    
    # Generate content
    content = generate_product_content(product)
    
    # Get all categories for navigation
    all_categories = ProductCategory.query.filter_by(status='active').all()
    
    return render_template(
        'product.html',
        product=product,
        related_products=related_products,
        faqs=faqs,
        content=content,
        categories=all_categories
    )


@app.route("/category/<slug>")
def category_page(slug):
    """Category page with SEO-friendly URL"""
    category = ProductCategory.query.filter_by(slug=slug, status='active').first()
    
    if not category:
        abort(404)
    
    # Get products in this category
    products = Product.query.filter_by(category=category.name, status='active').all()
    
    # Get subcategories
    subcategories = ProductCategory.query.filter_by(parent_id=category.id, status='active').all()
    
    # Generate meta content
    if not category.meta_title:
        category.meta_title = f"{category.name} | Precision Fasteners & Components | Nirmal Precision"
    if not category.meta_description:
        category.meta_description = f"Browse our comprehensive range of {category.name.lower()}. "
        category.meta_description += "Precision engineered components manufactured to DIN, ISO, and ASTM standards. "
        category.meta_description += "ISO 9001:2015 certified. Global export to 80+ countries."
    
    return render_template(
        'category.html',
        category=category,
        products=products,
        subcategories=subcategories
    )


@app.route("/material/<slug>")
def material_page(slug):
    """Material page with SEO-friendly URL"""
    material = Material.query.filter_by(slug=slug, status='active').first()
    
    if not material:
        abort(404)
    
    # Get products with this material
    products = Product.query.filter(
        Product.materials.contains(material.name),
        Product.status == 'active'
    ).all()
    
    # Parse lists
    material_properties = material.properties.split('\n') if material.properties else []
    material_applications = material.applications.split('\n') if material.applications else []
    material_advantages = material.advantages.split('\n') if material.advantages else []
    material_industries = material.industries.split('\n') if material.industries else []
    
    return render_template(
        'material.html',
        material=material,
        products=products,
        properties=material_properties,
        applications=material_applications,
        advantages=material_advantages,
        industries=material_industries
    )


@app.route("/industry/<slug>")
def industry_page(slug):
    """Industry page with SEO-friendly URL"""
    industry = Industry.query.filter_by(slug=slug, status='active').first()
    
    if not industry:
        abort(404)
    
    # Get products related to this industry
    industry_products = []
    if industry.products:
        keywords = industry.products.lower().split(',')
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                found = Product.query.filter(
                    Product.industries.contains(keyword),
                    Product.status == 'active'
                ).all()
                for p in found:
                    if p not in industry_products:
                        industry_products.append(p)
    
    # Parse lists
    industry_applications = industry.applications.split('\n') if industry.applications else []
    
    return render_template(
        'industry.html',
        industry=industry,
        products=industry_products[:12],
        applications=industry_applications
    )


@app.route("/search")
def search():
    """Enhanced search with DIN/ISO support"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    material = request.args.get('material', '')
    standard = request.args.get('standard', '')
    
    products_query = Product.query.filter(Product.status == 'active')
    
    if query:
        # Search in name, code, descriptions, standards
        search_filter = (
            Product.name.contains(query) |
            Product.code.contains(query) |
            Product.short_description.contains(query) |
            Product.din_standard.contains(query) |
            Product.iso_standard.contains(query) |
            Product.astm_standard.contains(query) |
            Product.keywords.contains(query)
        )
        products_query = products_query.filter(search_filter)
    
    if category:
        products_query = products_query.filter(Product.category == category)
    
    if material:
        products_query = products_query.filter(
            Product.materials.contains(material) |
            Product.material.contains(material)
        )
    
    if standard:
        standard_filter = (
            Product.din_standard.contains(standard) |
            Product.iso_standard.contains(standard) |
            Product.astm_standard.contains(standard)
        )
        products_query = products_query.filter(standard_filter)
    
    products = products_query.all()
    
    # Get all categories for filters
    all_categories = ProductCategory.query.filter_by(status='active').all()
    
    return render_template(
        'search.html',
        products=products,
        query=query,
        selected_category=category,
        selected_material=material,
        selected_standard=standard,
        categories=all_categories
    )


# ======================
# ADMIN: PRODUCT MANAGEMENT
# ======================

@app.route("/admin/products")
def admin_products():
    """Product management page"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin_products.html', products=products)


@app.route("/admin/product/add", methods=["GET", "POST"])
def admin_product_add():
    """Add new product"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    if request.method == "POST":
        # Generate slug from name and standard
        slug_base = slugify(request.form.get('name', ''))
        standard = request.form.get('din_standard') or request.form.get('iso_standard') or ''
        slug = f"{slugify(standard)}-{slug_base}" if standard else slug_base
        
        # Ensure unique slug
        existing = Product.query.filter_by(slug=slug).first()
        counter = 1
        base_slug = slug
        while existing:
            slug = f"{base_slug}-{counter}"
            existing = Product.query.filter_by(slug=slug).first()
            counter += 1
        
        # Handle image
        image_path = ''
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_path = os.path.join(app.root_path, 'static', 'img', 'products', filename)
                file.save(upload_path)
                image_path = f'/static/img/products/{filename}'
        
        # Create product
        product = Product(
            code=request.form.get('code'),
            name=request.form.get('name'),
            slug=slug,
            din_standard=request.form.get('din_standard'),
            iso_standard=request.form.get('iso_standard'),
            astm_standard=request.form.get('astm_standard'),
            category=request.form.get('category'),
            subcategory=request.form.get('subcategory'),
            short_description=request.form.get('short_description'),
            long_description=request.form.get('long_description'),
            applications=request.form.get('applications'),
            industries=request.form.get('industries'),
            materials=request.form.get('materials'),
            surface_finish=request.form.get('surface_finish'),
            available_sizes=request.form.get('available_sizes'),
            thread_types=request.form.get('thread_types'),
            manufacturing_process=request.form.get('manufacturing_process'),
            tolerance=request.form.get('tolerance'),
            quality_standards=request.form.get('quality_standards'),
            technical_specifications=request.form.get('technical_specifications'),
            material=request.form.get('material'),
            size=request.form.get('size'),
            standard=request.form.get('standard'),
            meta_title=request.form.get('meta_title'),
            meta_description=request.form.get('meta_description'),
            keywords=request.form.get('keywords'),
            image=image_path,
            status=request.form.get('status', 'active')
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!')
        return redirect(url_for('admin_products'))
    
    categories = ProductCategory.query.filter_by(status='active').all()
    return render_template('admin_product_form.html', product=None, categories=categories)


@app.route("/admin/product/<int:id>/edit", methods=["GET", "POST"])
def admin_product_edit(id):
    """Edit existing product"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    product = Product.query.get(id)
    if not product:
        abort(404)
    
    if request.method == "POST":
        product.code = request.form.get('code')
        product.name = request.form.get('name')
        product.din_standard = request.form.get('din_standard')
        product.iso_standard = request.form.get('iso_standard')
        product.astm_standard = request.form.get('astm_standard')
        product.category = request.form.get('category')
        product.subcategory = request.form.get('subcategory')
        product.short_description = request.form.get('short_description')
        product.long_description = request.form.get('long_description')
        product.applications = request.form.get('applications')
        product.industries = request.form.get('industries')
        product.materials = request.form.get('materials')
        product.surface_finish = request.form.get('surface_finish')
        product.available_sizes = request.form.get('available_sizes')
        product.thread_types = request.form.get('thread_types')
        product.manufacturing_process = request.form.get('manufacturing_process')
        product.tolerance = request.form.get('tolerance')
        product.quality_standards = request.form.get('quality_standards')
        product.technical_specifications = request.form.get('technical_specifications')
        product.material = request.form.get('material')
        product.size = request.form.get('size')
        product.standard = request.form.get('standard')
        product.meta_title = request.form.get('meta_title')
        product.meta_description = request.form.get('meta_description')
        product.keywords = request.form.get('keywords')
        product.status = request.form.get('status', 'active')
        
        # Handle new image
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_path = os.path.join(app.root_path, 'static', 'img', 'products', filename)
                file.save(upload_path)
                product.image = f'/static/img/products/{filename}'
        
        # Update slug if name changed
        if request.form.get('update_slug'):
            slug_base = slugify(request.form.get('name', ''))
            standard = request.form.get('din_standard') or request.form.get('iso_standard') or ''
            new_slug = f"{slugify(standard)}-{slug_base}" if standard else slug_base
            product.slug = new_slug
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Product updated successfully!')
        return redirect(url_for('admin_products'))
    
    categories = ProductCategory.query.filter_by(status='active').all()
    return render_template('admin_product_form.html', product=product, categories=categories)


@app.route("/admin/product/<int:id>/delete")
def admin_product_delete(id):
    """Delete product"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!')
    
    return redirect(url_for('admin_products'))


@app.route("/admin/product/<int:id>/faqs")
def admin_product_faqs(id):
    """Manage product FAQs"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    product = Product.query.get(id)
    if not product:
        abort(404)
    
    faqs = ProductFAQ.query.filter_by(product_id=id).order_by(ProductFAQ.order).all()
    
    return render_template('admin_product_faqs.html', product=product, faqs=faqs)


@app.route("/admin/product/<int:id>/faq/add", methods=["POST"])
def admin_product_faq_add(id):
    """Add FAQ to product"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    faq = ProductFAQ(
        product_id=id,
        question=request.form.get('question'),
        answer=request.form.get('answer'),
        order=int(request.form.get('order', 0))
    )
    db.session.add(faq)
    db.session.commit()
    
    flash('FAQ added successfully!')
    return redirect(url_for('admin_product_faqs', id=id))


@app.route("/admin/product/<int:id>/faq/<int:faq_id>/delete")
def admin_product_faq_delete(id, faq_id):
    """Delete product FAQ"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    faq = ProductFAQ.query.get(faq_id)
    if faq:
        db.session.delete(faq)
        db.session.commit()
        flash('FAQ deleted successfully!')
    
    return redirect(url_for('admin_product_faqs', id=id))


# ======================
# ADMIN: CATEGORY MANAGEMENT
# ======================

@app.route("/admin/categories")
def admin_categories():
    """Category management page"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    categories = ProductCategory.query.order_by(ProductCategory.order).all()
    return render_template('admin_categories.html', categories=categories)


@app.route("/admin/category/add", methods=["POST"])
def admin_category_add():
    """Add new category"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    slug = slugify(request.form.get('name', ''))
    
    category = ProductCategory(
        name=request.form.get('name'),
        slug=slug,
        description=request.form.get('description'),
        meta_title=request.form.get('meta_title'),
        meta_description=request.form.get('meta_description'),
        order=int(request.form.get('order', 0))
    )
    
    db.session.add(category)
    db.session.commit()
    
    flash('Category added successfully!')
    return redirect(url_for('admin_categories'))


# ======================
# ADMIN: MATERIAL MANAGEMENT
# ======================

@app.route("/admin/materials")
def admin_materials():
    """Material management page"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    materials = Material.query.all()
    return render_template('admin_materials.html', materials=materials)


@app.route("/admin/material/add", methods=["POST"])
def admin_material_add():
    """Add new material"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    slug = slugify(request.form.get('name', ''))
    
    material = Material(
        name=request.form.get('name'),
        slug=slug,
        description=request.form.get('description'),
        properties=request.form.get('properties'),
        applications=request.form.get('applications'),
        advantages=request.form.get('advantages'),
        industries=request.form.get('industries'),
        meta_title=request.form.get('meta_title'),
        meta_description=request.form.get('meta_description')
    )
    
    db.session.add(material)
    db.session.commit()
    
    flash('Material added successfully!')
    return redirect(url_for('admin_materials'))


# ======================
# ADMIN: INDUSTRY MANAGEMENT
# ======================

@app.route("/admin/industries")
def admin_industries():
    """Industry management page"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    industries = Industry.query.all()
    return render_template('admin_industries.html', industries=industries)


@app.route("/admin/industry/add", methods=["POST"])
def admin_industry_add():
    """Add new industry"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    slug = slugify(request.form.get('name', ''))
    
    industry = Industry(
        name=request.form.get('name'),
        slug=slug,
        description=request.form.get('description'),
        applications=request.form.get('applications'),
        products=request.form.get('products'),
        meta_title=request.form.get('meta_title'),
        meta_description=request.form.get('meta_description')
    )
    
    db.session.add(industry)
    db.session.commit()
    
    flash('Industry added successfully!')
    return redirect(url_for('admin_industries'))


# ======================
# ADMIN: BLOG MANAGEMENT
# ======================

@app.route("/admin/blog")
def admin_blog():
    """Blog management page"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin_blog.html', posts=posts)


@app.route("/admin/blog/add", methods=["GET", "POST"])
def admin_blog_add():
    """Add new blog post"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    if request.method == "POST":
        slug = slugify(request.form.get('title', ''))
        
        # Ensure unique slug
        existing = BlogPost.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{int(time.time())}"
        
        post = BlogPost(
            title=request.form.get('title'),
            slug=slug,
            content=request.form.get('content'),
            excerpt=request.form.get('excerpt'),
            category=request.form.get('category'),
            tags=request.form.get('tags'),
            author=request.form.get('author'),
            status=request.form.get('status', 'draft'),
            published_at=datetime.utcnow() if request.form.get('status') == 'published' else None,
            meta_title=request.form.get('meta_title'),
            meta_description=request.form.get('meta_description')
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin_blog_form.html', post=None)


@app.route("/admin/blog/edit/<int:id>", methods=["GET", "POST"])
def admin_blog_edit(id):
    """Edit existing blog post"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    post = BlogPost.query.get_or_404(id)
    
    if request.method == "POST":
        post.title = request.form.get('title')
        post.excerpt = request.form.get('excerpt')
        post.content = request.form.get('content')
        post.category = request.form.get('category')
        post.tags = request.form.get('tags')
        post.author = request.form.get('author')
        post.status = request.form.get('status', 'draft')
        post.published_at = datetime.utcnow() if request.form.get('status') == 'published' and not post.published_at else post.published_at
        post.meta_title = request.form.get('meta_title')
        post.meta_description = request.form.get('meta_description')
        
        db.session.commit()
        
        flash('Blog post updated successfully!')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin_blog_form.html', post=post)


@app.route("/admin/blog/delete/<int:id>", methods=["POST"])
def admin_blog_delete(id):
    """Delete a blog post"""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post deleted successfully!')
    return redirect(url_for('admin_blog'))


# ======================
# DYNAMIC SITEMAP UPDATE
# ======================

@app.route("/sitemap-dynamic.xml")
def sitemap_dynamic():
    """Generate comprehensive dynamic sitemap"""
    from flask import Response
    
    xml_sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
'''
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Static pages
    static_pages = [
        {"loc": "https://nirmalprecision.com/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "https://nirmalprecision.com/about", "priority": "0.8", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/products", "priority": "0.9", "changefreq": "daily"},
        {"loc": "https://nirmalprecision.com/export", "priority": "0.8", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/contact", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "https://nirmalprecision.com/blog", "priority": "0.6", "changefreq": "weekly"},
    ]
    
    for page in static_pages:
        xml_sitemap += f'''    <url>
        <loc>{page["loc"]}</loc>
        <priority>{page["priority"]}</priority>
        <changefreq>{page["changefreq"]}</changefreq>
        <lastmod>{today}</lastmod>
    </url>
'''
    
    # Products with slugs
    products = Product.query.filter_by(status='active').all()
    for product in products:
        if product.slug:
            xml_sitemap += f'''    <url>
        <loc>https://nirmalprecision.com/products/{product.slug}</loc>
        <priority>0.8</priority>
        <changefreq>weekly</changefreq>
        <lastmod>{product.updated_at.strftime('%Y-%m-%d') if product.updated_at else today}</lastmod>
    </url>
'''
    
    # Categories
    categories = ProductCategory.query.filter_by(status='active').all()
    for cat in categories:
        xml_sitemap += f'''    <url>
        <loc>https://nirmalprecision.com/category/{cat.slug}</loc>
        <priority>0.7</priority>
        <changefreq>weekly</changefreq>
        <lastmod>{today}</lastmod>
    </url>
'''
    
    # Materials
    materials = Material.query.filter_by(status='active').all()
    for mat in materials:
        xml_sitemap += f'''    <url>
        <loc>https://nirmalprecision.com/material/{mat.slug}</loc>
        <priority>0.6</priority>
        <changefreq>monthly</changefreq>
        <lastmod>{today}</lastmod>
    </url>
'''
    
    # Industries
    industries = Industry.query.filter_by(status='active').all()
    for ind in industries:
        xml_sitemap += f'''    <url>
        <loc>https://nirmalprecision.com/industry/{ind.slug}</loc>
        <priority>0.6</priority>
        <changefreq>monthly</changefreq>
        <lastmod>{today}</lastmod>
    </url>
'''
    
    # Blog posts
    posts = BlogPost.query.filter_by(status='published').all()
    for post in posts:
        if post.published_at:
            xml_sitemap += f'''    <url>
        <loc>https://nirmalprecision.com/blog/{post.slug}</loc>
        <priority>0.5</priority>
        <changefreq>monthly</changefreq>
        <lastmod>{post.updated_at.strftime('%Y-%m-%d') if post.updated_at else today}</lastmod>
    </url>
'''
    
    xml_sitemap += '</urlset>'
    
    return Response(xml_sitemap, mimetype='application/xml')


if __name__ == "__main__":
    app.run(debug=True)