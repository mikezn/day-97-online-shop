import random
from faker import Faker
from werkzeug.security import generate_password_hash
from shop import create_shop, db
from shop.models import Role, User, Product

app = create_shop()
fake = Faker()


def clear_tables():
    User.query.delete()
    db.session.commit()


def seed_roles():
    roles_to_seed = [
        {"role": "admin", "is_admin": True},
        {"role": "customer", "is_admin": False}
    ]

    for role_data in roles_to_seed:
        existing = Role.query.filter_by(role=role_data["role"]).first()
        if not existing:
            db.session.add(Role(role=role_data["role"], is_admin=role_data["is_admin"]))
    db.session.commit()
    print("✅ Roles seeded")


def seed_users():
    admin_role = Role.query.filter_by(role="admin").first()
    customer_role = Role.query.filter_by(role="customer").first()

    if not admin_role or not customer_role:
        print("❌ Roles missing. Seed roles first.")
        return

    # Admin user
    if not User.query.filter_by(email="admin@example.com").first():
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=generate_password_hash("adminpass"),
            role_id=admin_role.role_id
        )
        db.session.add(admin_user)

    # Sample users
    for i in range(9):
        email = f"user{i}@example.com"
        if User.query.filter_by(email=email).first():
            continue

        user = User(
            name=fake.name(),
            email=email,
            password=generate_password_hash("userpass"),
            role_id=customer_role.role_id
        )
        db.session.add(user)

    db.session.commit()
    print("✅ Users created (skipping duplicates)")


def seed_products():
    sample_products = [
        {
            "name": "Sample Tee",
            "description": "A basic cotton T-shirt",
            "price": 19.99,
            "img_url": "https://www.dmpauthority.com/cdn/shop/files/Cajon_Scaled_New.png?v=1725863081&width=823"
        },
        {
            "name": "Sample Tee 2",
            "description": "Long pants",
            "price": 39.99,
            "img_url": "https://www.dmpauthority.com/cdn/shop/files/Heavyweight_4_Scaled_New.png?v=1722393478&width=823"
        },
        {
            "name": "New sleeves",
            "description": "Long shirt",
            "price": 100.99,
            "img_url": "https://www.dmpauthority.com/cdn/shop/files/808Heavyweight_FINAL_Colorized_new.png?v=1715692586&width=823"
        },
    ]

    for item in sample_products:
        if Product.query.filter_by(name=item["name"]).first():
            continue
        product = Product(
            name=item["name"],
            description=item["description"],
            price=item["price"],
            img_url=item["img_url"]
        )
        db.session.add(product)

    db.session.commit()
    print("✅ Products created (skipping duplicates)")


def seed_all():
    seed_roles()
    seed_users()
    seed_products()


with app.app_context():
    db.create_all()
    print("✅ Database tables created.")
    clear_tables()
    seed_all()
    print("✅ Temp data inserted.")
