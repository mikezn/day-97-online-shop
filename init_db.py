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
    admin_role = Role(is_admin=True)
    user_role = Role(is_admin=False)
    db.session.add_all([admin_role, user_role])
    db.session.commit()
    print("✅ Roles created")


def seed_users():
    roles = Role.query.all()
    if not roles:
        print("❌ No roles found — run seed_roles() first")
        return

    admin_user = User(
        name="Admin User",
        email="admin@example.com",
        password=generate_password_hash("adminpass"),
        role_id=next(r.role_id for r in roles if r.is_admin)
    )
    db.session.add(admin_user)

    for i in range(9):
        user = User(
            name=fake.name(),
            email=f"user{i}@example.com",
            password=generate_password_hash("userpass"),
            role_id=next(r.role_id for r in roles if not r.is_admin)
        )
        db.session.add(user)

    db.session.commit()
    print("✅ Users created")


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
        # ... other products ...
    ]

    for item in sample_products:
        existing = Product.query.filter_by(name=item["name"]).first()
        if existing:
            continue  # Skip duplicates

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
    print("Database tables created.")
    clear_tables()
    seed_all()
    print("Temp data inserted")
