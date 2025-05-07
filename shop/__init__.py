from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
import hashlib
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
paypal_client = None

def create_shop():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Jinja filter
    def gravatar_hash(email):
        return hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()

    app.jinja_env.filters['hash'] = gravatar_hash

    # Initialize PayPal Client
    global paypal_client
    environment = SandboxEnvironment(
        client_id=os.getenv("PAYPAL_CLIENT_ID"),
        client_secret=os.getenv("PAYPAL_CLIENT_SECRET")
    ) if os.getenv("PAYPAL_ENVIRONMENT") == "sandbox" else LiveEnvironment(
        client_id=os.getenv("PAYPAL_CLIENT_ID"),
        client_secret=os.getenv("PAYPAL_CLIENT_SECRET")
    )

    paypal_client = PayPalHttpClient(environment)

    # Context Processor for PayPal Client ID
    @app.context_processor
    def inject_paypal_client_id():
        return {"PAYPAL_CLIENT_ID": os.getenv("PAYPAL_CLIENT_ID")}

    # Import and register blueprints
    from .routes import shop_bp
    app.register_blueprint(shop_bp, url_prefix="/shop")

    from .public_routes import public_bp
    app.register_blueprint(public_bp)

    return app
