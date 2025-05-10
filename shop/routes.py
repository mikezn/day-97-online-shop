from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import current_user
from .models import Product, User, Role, Order
from .forms import CreateProductForm, CreateUserForm
from . import db
from functools import wraps

shop_bp = Blueprint("shop", __name__, template_folder="templates")


# used as a decorator to only return the route function if it's an admin user
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.role.role != 'admin':
            print("NOT ADMIN")
            return abort(403)
        # Otherwise continue with the route function
        print("ADMIN ACCESS")
        return f(*args, **kwargs)
    return decorated_function


@shop_bp.route("/product", methods=["GET", "POST"])
@shop_bp.route("/product/<int:product_id>", methods=["GET", "POST"])
@admin_only
def manage_product(product_id=None):
    if product_id:
        product = Product.query.get_or_404(product_id)
        form = CreateProductForm(obj=product)
    else:
        product = None
        form = CreateProductForm()

    if form.validate_on_submit():
        if product:
            form.populate_obj(product)
            flash("Product updated!", "success")
        else:
            new_product = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                img_url=form.img_url.data
            )
            db.session.add(new_product)
            flash("Product added!", "success")

        db.session.commit()
        return redirect(url_for("shop.manage_product"))

    return render_template("product_form.html", form=form, product=product)

@shop_bp.route("/products", methods=["GET"])
@admin_only
def view_products():
    products = Product.query.all()
    return render_template("product_list.html", products=products)


@shop_bp.route("/customers", methods=["GET"])
@admin_only
def view_customers():
    customers = db.session.query(User).join(Role).filter(Role.is_admin == False).all()
    return render_template("customer_list.html", customers=customers)


@shop_bp.route("/customer", methods=["GET", "POST"])
@shop_bp.route("/customer/<int:user_id>", methods=["GET", "POST"])
@admin_only
def manage_customer(user_id=None):
    user = User.query.get(user_id) if user_id else None
    form = CreateUserForm(obj=user)

    # Populate role choices
    form.role_id.choices = [(role.role_id, "Admin" if role.is_admin else "User") for role in Role.query.all()]

    if form.validate_on_submit():
        if user:
            user.name = form.name.data
            user.email = form.email.data
            user.role_id = form.role_id.data
            # only update password if changed
            if form.password.data:
                user.password = form.password.data  # hash this in production!
            flash("Customer updated!", "success")
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,  # hash this in production!
                role_id=form.role_id.data
            )
            db.session.add(user)
            flash("Customer created!", "success")

        db.session.commit()
        return redirect(url_for("shop.customers_list"))

    return render_template("manage_customer.html", form=form, user=user)


@shop_bp.route("/orders")
@admin_only
def view_orders():
    # Ensure only admins can access
    if not current_user.role.is_admin:
        flash("Access restricted to admins only.")
        return redirect(url_for("public.store_home"))

    # Fetch all orders with user and product information
    orders = db.session.query(Order).join(User).order_by(Order.order_id.desc()).all()

    # Calculate total for each order
    order_summaries = []
    for order in orders:
        total = sum(item.quantity * item.product.price for item in order.order_products)
        order_summaries.append({
            "order": order,
            "customer": order.user.name,
            "total": total
        })

    return render_template("order_list.html", order_summaries=order_summaries)


@shop_bp.route("/admin/orders/<int:order_id>")
@admin_only
def view_order_detail(order_id):
    # Ensure only admins can access
    if not current_user.role.is_admin:
        flash("Access restricted to admins only.")
        return redirect(url_for("public.store_home"))

    order = Order.query.get_or_404(order_id)
    total = sum(item.quantity * item.product.price for item in order.order_products)

    return render_template("order_detail.html", order=order, total=total)