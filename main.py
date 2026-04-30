from time import time

from flask import Flask, redirect, render_template, request, url_for, session
from models import db, Product, Users, CartItem, WishlistItem
import os
from dotenv import load_dotenv
from sqlalchemy import or_

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)
try:
    import stripe
except ImportError:
    stripe = None

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Olatunde'  # Change this to a random secret key in production!
stripe_api_key = os.environ.get('STRIPE_API_KEY')
if stripe is not None and stripe_api_key:
    stripe.api_key = stripe_api_key
else:
    if stripe is None:
        app.logger.warning('Stripe package is not installed. Stripe checkout is disabled.')
    elif not stripe_api_key:
        app.logger.warning('Stripe API key is not configured. Set STRIPE_API_KEY in the environment.')

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(user_id):
    return db.get_or_404(Users, int(user_id))


@app.route("/")
def home():
    all_products = Product.query.all()
    max_price_diff = 0
    max_price_diff_product = None
    for product in all_products:
        if product.old_price and product.price:
            price_diff = product.old_price - product.price
            if price_diff > max_price_diff:
                max_price_diff = price_diff
                max_price_diff_product = product
    new_arrivals = Product.query.filter_by(is_new_arrival=True).all()
    featured_products = Product.query.filter_by(is_featured=True).all()
    top_selling = Product.query.filter_by(is_top_selling=True).all()
    wishlist_product_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []

    return render_template(
        "index.html",
        all_products=all_products,
        new_arrivals=new_arrivals,
        featured_products=featured_products,
        top_selling=top_selling,
        max_price_diff_product=max_price_diff_product,
        max_price_diff=max_price_diff,
        logged_in=current_user.is_authenticated,
        wishlist_product_ids=wishlist_product_ids
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Handle login logic here (e.g., form validation, user authentication)
        user = Users.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect(url_for('home', logged_in=True))
        else:
            return "Invalid email or password!"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    form_data = {
        "first_name": "",
        "last_name": "",
        "email": ""
    }

    if request.method == "POST":
        form_data["first_name"] = request.form.get("first_name", "").strip()
        form_data["last_name"] = request.form.get("last_name", "").strip()
        form_data["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            error = "Passwords do not match!"
        elif not (form_data["first_name"] and form_data["last_name"] and form_data["email"] and password):
            error = "All fields are required."
        else:
            username = f"{form_data['last_name']} {form_data['first_name']}"
            if Users.query.filter_by(email=form_data["email"]).first():
                error = "That email is already registered. Please log in or use another email."
            else:
                hashed_and_salted_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                new_user = Users(
                    username=username,
                    email=form_data["email"],
                    password_hash=hashed_and_salted_password
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('home', logged_in=True))

    return render_template("register.html", error=error, **form_data)

@app.route("/wishlist")
@login_required
def wishlist():
    wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template("wishlist.html", wishlist_items=wishlist_items, logged_in=current_user.is_authenticated)


def get_cart_data():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    items = []
    subtotal = 0.0
    for cart_item in cart_items:
        product = cart_item.product
        total = product.price * cart_item.quantity
        items.append({
            "product": product,
            "quantity": cart_item.quantity,
            "total": total,
            "cart_item": cart_item
        })
        subtotal += total
    shipping = 3.0 if subtotal > 0 else 0.0
    return items, subtotal, shipping


@app.route("/cart")
@login_required
def cart():
    cart_items, subtotal, shipping = get_cart_data()
    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        shipping=shipping,
        total=subtotal + shipping,
        logged_in=current_user.is_authenticated
    )


@app.route("/cart/add/<int:product_id>")
@login_required
def add_to_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    return redirect( url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
@login_required
def update_cart():
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity", 1))
    if product_id:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=int(product_id)).first()
        if cart_item:
            if quantity > 0:
                cart_item.quantity = quantity
            else:
                db.session.delete(cart_item)
            db.session.commit()
    return redirect(url_for("cart"))


@app.route("/all_wishlist")
@login_required
def all_wishlist():
    wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template("wishlist.html", wishlist_items=wishlist_items, logged_in=current_user.is_authenticated)


@app.route("/wishlist/add/<int:product_id>")
@login_required
def add_to_wishlist(product_id):
    wishlist_item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not wishlist_item:
        wishlist_item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
    return redirect(request.referrer or url_for("wishlist"))


@app.route("/wishlist/remove/<int:product_id>")
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
    return redirect(url_for("wishlist"))

@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


def normalize_category(category):
    if not category:
        return "all"
    category = category.strip().lower()
    known = {
        "all category": "all",
        "all": "all",
        "accessories": "accessories",
        "electronics": "electronics",
        "laptop": "laptop",
        "laptops & desktops": "laptop",
        "laptops and desktops": "laptop",
        "mobiles & tablets": "mobiles & tablets",
        "mobiles and tablets": "mobiles & tablets",
        "smartphone": "smartphone",
        "smartphone & smart tv": "smartphone",
        "smartphone and smart tv": "smartphone",
        "smart phone": "smartphone",
        "smart camera": "smart camera"
    }
    return known.get(category, category)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    raw_category = request.args.get("category", "all")
    category = normalize_category(raw_category)

    products_query = Product.query
    if category != "all":
        products_query = products_query.filter(Product.category.ilike(f"%{category}%"))
    if query:
        like_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(like_pattern),
                Product.description.ilike(like_pattern),
                Product.category.ilike(like_pattern)
            )
        )

    products = products_query.all()
    if query and category != "all":
        description = f"Search results for '{query}' in {raw_category}"
    elif query:
        description = f"Search results for '{query}'"
    elif category != "all":
        description = f"{raw_category}"
    else:
        description = "All Products"

    featured_products = Product.query.filter_by(is_featured=True).all()
    no_products = len(products) == 0
    search_query = query if query else None
    wishlist_product_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    return render_template(
        "shop.html",
        products=products,
        description=description,
        featured_products=featured_products[:10],
        category=raw_category,
        no_products=no_products,
        search_query=search_query,
        wishlist_product_ids=wishlist_product_ids,
        logged_in=current_user.is_authenticated
    )


@app.route("/product/<int:product_id>")
def product(product_id):
    product = Product.query.get_or_404(product_id)
    featured_products = Product.query.filter_by(is_featured=True).all()
    related_products = Product.query.filter_by(category=product.category).filter(Product.id != product.id).all()
    wishlist_product_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    return render_template("single.html", product=product, featured_products=featured_products[:10], related_products=related_products[:10], wishlist_product_ids=wishlist_product_ids, logged_in=current_user.is_authenticated)


@app.route("/shop/<string:category>")
def shop(category):
    description = ""
    if category == "all":
        products = Product.query.all()
    elif category == "sale":
        products = Product.query.filter_by(label="Sale").all()
        description = "Find all products available on the sale promo here"
    elif category == "featured":
        products = Product.query.filter_by(is_featured=True).all()
        description = "Find all featured products here"
    elif category == "accessories":
        products = Product.query.filter_by(category="Accessories").all()
        description = "Find all accessories here"
    elif category == "electronics":
        products = Product.query.filter_by(category="smart camera").all()
        products += Product.query.filter_by(category="smart watch").all()
        description = "Find all electronics here"
    elif category == "smart camera":
        products = Product.query.filter_by(category="Smart camera").all()
        description = "Find all smart cameras here"
    elif category == "smart watch":
        products = Product.query.filter_by(category="Smart Watch").all()
        description = "Find all smart watches here"
    elif category == "laptop and desktops":
        products = Product.query.filter_by(category="Laptop").all()
        products += Product.query.filter_by(category="Desktop").all()
        description = "Find all laptops and desktops here"
    elif category == "mobiles and tablets":
        products = Product.query.filter_by(category="Mobile").all()
        products += Product.query.filter_by(category="Tablet").all()
        description = "Find all mobiles and tablets here"
    elif category == "smartphone and smart tv":
        products = Product.query.filter_by(category="SmartPhone").all()
        products += Product.query.filter_by(category="Smart TV").all()
        description = "Find all smartphones and smart TVs here"
    else:
        products = Product.query.filter_by(category=category).all()
    if description == "":
        description = f"Find your {category} here"
    featured_products = Product.query.filter_by(is_featured=True).all()
    no_products = len(products) == 0
    wishlist_product_ids = [item.product_id for item in WishlistItem.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    return render_template("shop.html", products=products, description=description, featured_products=featured_products[:10], category=category, no_products=no_products, wishlist_product_ids=wishlist_product_ids, logged_in=current_user.is_authenticated)


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items, subtotal, shipping = get_cart_data()
    if request.method == "POST":
        order_data = {
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "company_name": request.form.get("company_name"),
            "address": request.form.get("address"),
            "city": request.form.get("city"),
            "country": request.form.get("country"),
            "postcode": request.form.get("postcode"),
            "mobile": request.form.get("mobile"),
            "email": request.form.get("email"),
            "create_account": request.form.get("create_account") == "yes",
            "ship_different_address": request.form.get("ship_different_address") == "yes",
            "order_notes": request.form.get("order_notes"),
            "payment_method": request.form.get("payment_method")
        }
        app.logger.info("Checkout form submitted: %s", order_data)
        if stripe is None:
            app.logger.error('Stripe package is not installed. Checkout cannot proceed.')
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                subtotal=subtotal,
                shipping=shipping,
                total=subtotal + shipping,
                logged_in=current_user.is_authenticated,
                error="Payment is unavailable because the Stripe dependency is missing."
            )
        if not stripe_api_key:
            app.logger.error('Stripe API key is not configured. Checkout cannot proceed.')
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                subtotal=subtotal,
                shipping=shipping,
                total=subtotal + shipping,
                logged_in=current_user.is_authenticated,
                error="Payment is unavailable because Stripe is not configured."
            )

        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item["product"].name,
                    },
                    'unit_amount': int(item["product"].price * 100),  # Stripe expects amounts in cents
                },
                'quantity': item["quantity"],
            })
        
        # Add shipping as a line item if applicable
        if shipping > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Shipping',
                    },
                    'unit_amount': int(shipping * 100),
                },
                'quantity': 1,
            })
        order_reference = f"ORDER-{int(time())}-{current_user.id}"
        
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode='payment',
                payment_method_types=['card'],  # Add this back for older API versions
                success_url=url_for('order_success', order_ref=order_reference, _external=True),
                cancel_url=url_for('order_cancel', _external=True),
                metadata={
                    'user_id': current_user.id,
                    'user_email': current_user.email,
                    'order_reference': order_reference,
                    'shipping_address': f"{order_data['address']}, {order_data['city']}, {order_data['country']}",
                    'customer_name': f"{order_data['first_name']} {order_data['last_name']}",
                    'order_notes': order_data.get('order_notes', '')[:500]  # Limit length
                }
            )
            if not checkout_session.url:
                app.logger.error("Stripe session created but no URL returned")
                raise Exception("Stripe session has no URL")
            return redirect(checkout_session.url)
        except stripe.error.CardError as e:
            app.logger.error(f"Stripe Card Error: {e.user_message}")
            error_msg = e.user_message
        except stripe.error.RateLimitError as e:
            app.logger.error("Stripe Rate Limit Error")
            error_msg = "Payment service is temporarily unavailable. Please try again in a moment."
        except stripe.error.InvalidRequestError as e:
            app.logger.error(f"Stripe Invalid Request: {str(e)}")
            error_msg = "Invalid payment request. Please check your information and try again."
        except stripe.error.AuthenticationError as e:
            app.logger.error(f"Stripe Authentication Error: {str(e)}")
            error_msg = "Payment service authentication failed. Please contact support."
        except stripe.error.APIConnectionError as e:
            app.logger.error(f"Stripe Connection Error: {str(e)}")
            error_msg = "Unable to connect to payment service. Please try again."
        except stripe.error.StripeError as e:
            app.logger.error(f"Stripe Error: {str(e)}")
            error_msg = "Payment processing failed. Please try again."
        except Exception as e:
            app.logger.error(f"Unexpected error during checkout: {str(e)}", exc_info=True)
            error_msg = "An unexpected error occurred. Please try again."
        
        return render_template(
            "checkout.html",
            cart_items=cart_items,
            subtotal=subtotal,
            shipping=shipping,
            total=subtotal + shipping,
            logged_in=current_user.is_authenticated,
            error=error_msg
        )
        # return render_template(
        #     "checkout.html",
        #     cart_items=cart_items,
        #     subtotal=subtotal,
        #     shipping=shipping,
        #     total=subtotal + shipping,
        #     logged_in=current_user.is_authenticated,
        #     order_data=order_data,
        #     order_submitted=True
        # )
    return render_template(
        "checkout.html",
        cart_items=cart_items,
        subtotal=subtotal,
        shipping=shipping,
        total=subtotal + shipping,
        logged_in=current_user.is_authenticated
    )


@app.route('/order_success')
def order_success():
    # Get the order reference from query params
    order_ref = request.args.get('order_ref')

    # Clear the cart after successful payment
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
    return render_template('order_success.html', order_reference=order_ref)

@app.route('/order_cancel')
def order_cancel():
    return render_template('order_cancel.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)