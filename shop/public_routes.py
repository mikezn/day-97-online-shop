from flask import Blueprint, render_template
from .models import Product

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def store_home():
    return render_template("store_home.html")

@public_bp.route('/products')
def store_products():
    products = Product.query.all()
    return render_template("store_products.html", products=products)


@public_bp.route('/product/<int:product_id>')
def store_product_detail():
    return render_template("store_products.html")