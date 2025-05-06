from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, login_required
from .models import db, Product, Order, OrderProduct, User, Role
from .forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from shop import login_manager

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
    try:
        new_quantity = int(request.form.get("quantity", 1))
    except ValueError:
        flash("Invalid quantity input.", "warning")
        return redirect(url_for("public.view_cart"))

    new_quantity = max(new_quantity, 0)  # clamp to 0
    print(new_quantity)

    cart = Order.query.filter_by(user_id=current_user.user_id, is_cart=True).first()
    if not cart:
        flash("Cart not found.", "error")
        return redirect(url_for("public.view_cart"))

    item = OrderProduct.query.filter_by(order_id=cart.order_id, product_id=product_id).first()
    if not item:
        flash("Item not found in your cart.", "error")
        return redirect(url_for("public.view_cart"))

    if new_quantity < 0:
        item.quantity = 0
    else:
        item.quantity = new_quantity
    print(item.quantity)
    db.session.commit()
    return redirect(url_for("public.view_cart"))
