from shop import create_shop, db

app = create_shop()

with app.app_context():
    db.create_all()
    print("Database tables created.")
