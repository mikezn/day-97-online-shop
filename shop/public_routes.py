from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_user, login_required
from .models import db, Product, Order, OrderProduct, User, Role
from .forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from shop import login_manager, paypal_client
from flask_wtf.csrf import generate_csrf
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
import json

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def store_home():
    return render_template("store_home.html")


@public_bp.route('/products')
def store_products():
    products = Product.query.all()
    return render_template("store_products.html", products=products)


@public_bp.route('/product/<int:product_id>')
def store_product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("store_product_detail.html", product=product)


@public_bp.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    #check if user has an active cart
    cart = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()

    # if no cart, create new one
    if not cart:
        cart = Order(user_id=current_user.user_id, is_cart=True)
        db.session.add(cart)
        db.session.flush()

    # check if product already in cart
    existing_item = OrderProduct.query.filter_by(order_id=cart.order_id, product_id=product_id).first()

    if existing_item:
        existing_item.quantity += 1
    else:
        new_item = OrderProduct(order_id=cart.order_id, product_id=product_id, quantity=1)
        db.session.add(new_item)

    db.session.commit()
    flash(f"Added '{product.name}' to your cart.", "info")
    return redirect(url_for("public.store_product_detail", product_id=product_id))


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@public_bp.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.store_home"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = db.session.scalar(db.select(User).where(User.email == form.email.data))

        if existing_user:
            flash("You've already signed up — please log in.")
            return redirect(url_for("public.login"))

        role = db.session.scalar(db.select(Role).where(Role.role == "customer"))
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            role_id=role.role_id,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("public.store_home"))

    return render_template("register.html", form=form)


@public_bp.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.store_home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))

        if not user:
            flash("No user found, please register")
        elif not check_password_hash(user.password, form.password.data):
            flash("Incorrect password... try again")
        else:
            login_user(user)
            return redirect(url_for("public.store_home"))

    return render_template("login.html", form=form)


@public_bp.route("/cart")
@login_required
def view_cart():
    cart = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()

    if not cart or not cart.order_products:
        return render_template("store_cart.html", items=[], total=0)

    items = cart.order_products  # or fetch joined data if needed
    total = sum(item.quantity * item.product.price for item in items)

    return render_template("store_cart.html", items=items, total=total)


@public_bp.route("/cart/update/<int:product_id>", methods=["POST"])
@login_required
def update_cart_quantity(product_id):

    # Read JSON data directly
    data = request.get_json()
    if not data:
        return {"error": "Invalid request"}, 400

    new_quantity = data.get("quantity", 1)

    if new_quantity is None or not isinstance(new_quantity, int):
        return {"error": "Invalid quantity"}, 400

    new_quantity = max(new_quantity, 0)

    cart = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()
    if not cart:
        return {"error": "Cart not found"}, 404

    item = OrderProduct.query.filter_by(order_id=cart.order_id, product_id=product_id).first()
    if not item:
        return {"error": "Item not found in your cart"}, 404

    if new_quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = new_quantity

    db.session.commit()
    return {"message": "Cart updated successfully"}, 200



@public_bp.route("/checkout")
@login_required
def checkout():
    return render_template("store_home")


@public_bp.route("/api/orders", methods=["POST"])
def create_paypal_order():
    print("✅ Received request to create PayPal order")

    try:
        raw_data = request.data
        print("✅ Raw Request Data:", raw_data)

        request_data = json.loads(raw_data)
        print("✅ JSON Request Data:", request_data)

        # If the cart is "current", we fetch the user's active cart
        if request_data.get("cart") == "current":
            cart = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()
            if not cart or not cart.order_products:
                return jsonify({"error": "Cart is empty"}), 400

            cart_items = [{
                "name": item.product.name,
                "unit_amount": {
                    "currency_code": "USD",
                    "value": str(item.product.price)
                },
                "quantity": str(item.quantity)
            } for item in cart.order_products]

            total_price = sum(float(item.product.price) * item.quantity for item in cart.order_products)
            print("✅ Cart Items:", cart_items)
            print("✅ Total Price:", total_price)
        else:
            return jsonify({"error": "Invalid cart format"}), 400

        # PayPal Order Request
        order_request = OrdersCreateRequest()
        order_request.prefer("return=representation")
        order_request.request_body({
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{total_price:.2f}",
                        "breakdown": {
                            "item_total": {
                                "currency_code": "USD",
                                "value": f"{total_price:.2f}"
                            }
                        }
                    },
                    "items": cart_items
                }
            ]
        })

        # Send request to PayPal
        response = paypal_client.execute(order_request)
        print("✅ PayPal Order Created:", response.result.id)

        return jsonify({"id": response.result.id})
    except Exception as e:
        print("❌ Exception during PayPal Order Creation:", str(e))
        return jsonify({"error": str(e)}), 500


@public_bp.route("/api/orders/<order_id>/capture", methods=["POST"])
@login_required
def capture_paypal_order(order_id):
    try:
        print(f"✅ Capturing PayPal Order: {order_id}")

        # Initialize PayPal capture request
        request_capture = OrdersCaptureRequest(order_id)
        request_capture.request_body({})  # Empty JSON body for capture

        # ✅ Use the global paypal_client directly
        response = paypal_client.execute(request_capture)
        print("✅ Raw PayPal Response:", response)
        result = response.result

        print(f"✅ Capture Result: {result.status}")

        # Extract purchase units and capture details
        captured_data = {
            "status": result.status,
            "id": result.id,
            "purchase_units": []
        }

        for unit in result.purchase_units:
            unit_data = {
                "amount": None,
                "currency": None,
                "items": []
            }

            # Access the captured payments
            if hasattr(unit, "payments") and hasattr(unit.payments, "captures"):
                for capture in unit.payments.captures:
                    unit_data["amount"] = capture.amount.value
                    unit_data["currency"] = capture.amount.currency_code

            captured_data["purchase_units"].append(unit_data)

        print("✅ Captured Order Data:", captured_data)

        # mark the user's cart order as completed
        cart_order = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()
        if cart_order:
            cart_order.is_cart = False
            db.session.commit()
            print("✅ Order marked as completed.")

        return jsonify(captured_data)
    except Exception as e:
        print("❌ Exception during PayPal Order Capture:", str(e))
        return jsonify({"error": str(e)}), 500


@public_bp.route('/get-csrf-token')
def get_csrf_token():
    from flask import jsonify
    token = generate_csrf()
    return jsonify({"csrf_token": token})
