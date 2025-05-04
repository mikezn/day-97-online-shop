from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import Product
from .forms import CreateProductForm
from . import db

shop_bp = Blueprint("shop", __name__, template_folder="templates")

@shop_bp.route("/product", methods=["GET", "POST"])
@shop_bp.route("/product/<int:product_id>", methods=["GET", "POST"])
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
def view_products():
    products = Product.query.all()
    return render_template("product_list.html", products=products)
