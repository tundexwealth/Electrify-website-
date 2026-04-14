from main import app
from models import db, Product, ProductImage, Users, CartItem
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    # Prevent duplicate seeding
    if Product.query.count() > 0:
        print("Products already exist.")
    else:
        products = [
            {
                "name": "Apple iphone 6",
                "category": "SmartPhone",
                "price": 1050.00,
                "old_price": 1250.00,
                "image": "img/product-3.png",
                "label": "New",
                "rating": 4,
                "description": "A powerful Apple iphone 6 device with sleek design and great performance.",
                "stock": 15,
                "is_new_arrival": True,
                "is_featured": True,
                "is_top_selling": True,
                "images": [
                    "img/product-3.png",
                    "img/product-4.png",
                    "img/product-5.png"
                ]
            },
            {
                "name": "Canon EOS M50",
                "category": "smart camera",
                "price": 980.00,
                "old_price": 1150.00,
                "image": "img/product-4.png",
                "label": "Sale",
                "rating": 5,
                "description": "A compact and stylish smart camera for modern users.",
                "stock": 10,
                "is_new_arrival": True,
                "is_featured": False,
                "is_top_selling": True,
                "images": [
                    "img/product-4.png",
                    "img/product-5.png",
                    "img/product-6.png"
                ]
            },
            {
                "name": "Canon camera lens G2358",
                "category": "smart camera",
                "price": 1120.00,
                "old_price": 1300.00,
                "image": "img/product-5.png",
                "label": None,
                "rating": 4,
                "description": "Premium Canon camera lens with impressive image quality.",
                "stock": 8,
                "is_new_arrival": False,
                "is_featured": True,
                "is_top_selling": False,
                "images": [
                    "img/product-5.png",
                    "img/product-6.png",
                    "img/product-7.png"
                ]
            },
            {
                "name": "Phone Holder G2359",
                "category": "Accessories",
                "price": 1040.00,
                "old_price": 1220.00,
                "image": "img/product-6.png",
                "label": "New",
                "rating": 4,
                "description": "Extremely reliable phone holder for everyday use.",
                "stock": 12,
                "is_new_arrival": False,
                "is_featured": True,
                "is_top_selling": True,
                "images": [
                    "img/product-6.png",
                    "img/product-7.png",
                    "img/product-11.png"
                ]
            },
            {
                "name": "Smart Camera",
                "category": "Smart camera",
                "price": 990.00,
                "old_price": 1190.00,
                "image": "img/product-7.png",
                "label": "Sale",
                "rating": 5,
                "description": "A bestselling smart camera with smooth performance.",
                "stock": 20,
                "is_new_arrival": True,
                "is_featured": False,
                "is_top_selling": True,
                "images": [
                    "img/product-7.png",
                    "img/product-11.png",
                    "img/product-3.png"
                ]
            },
            {
                "name": "KD Laptop",
                "category": "Laptop",
                "price": 1080.00,
                "old_price": 1280.00,
                "image": "img/product-11.png",
                "label": None,
                "rating": 4,
                "description": "A stylish laptop that performs really efficiently.",
                "stock": 6,
                "is_new_arrival": False,
                "is_featured": True,
                "is_top_selling": True,
                "images": [
                    "img/product-11.png",
                    "img/product-3.png",
                    "img/product-4.png"
                ]
            },
            {
                "name": "Desktop Computer",
                "category": "Desktop",
                "price": 1200.00,
                "old_price": 1400.00,
                "image": "img/product-12.png",
                "label": "New",
                "rating": 5,
                "description": "High-performance desktop computer for gaming and productivity.",
                "stock": 5,
                "is_new_arrival": True,
                "is_featured": True,
                "is_top_selling": False,
                "images": [
                    "img/product-12.png"
                ]
            },
            {
                "name": "Smart Watch",
                "category": "Smart Watch",
                "price": 250.00,
                "old_price": 300.00,
                "image": "img/product-13.png",
                "label": "Sale",
                "rating": 4,
                "description": "Feature-rich smart watch with health tracking and notifications.",
                "stock": 25,
                "is_new_arrival": True,
                "is_featured": False,
                "is_top_selling": True,
                "images": [
                    "img/product-13.png"
                ]
            },
            {
                "name": "Drone",
                "category": "Drone",
                "price": 500.00,
                "old_price": 600.00,
                "image": "img/product-14.png",
                "label": None,
                "rating": 4,
                "description": "Advanced drone with camera for aerial photography.",
                "stock": 10,
                "is_new_arrival": False,
                "is_featured": True,
                "is_top_selling": False,
                "images": [
                    "img/product-14.png"
                ]
            },
            {
                "name": "Gaming Headset",
                "category": "Accessories",
                "price": 80.00,
                "old_price": 100.00,
                "image": "img/product-8.png",
                "label": "Sale",
                "rating": 4,
                "description": "Comfortable gaming headset with surround sound.",
                "stock": 30,
                "is_new_arrival": False,
                "is_featured": False,
                "is_top_selling": True,
                "images": [
                    "img/product-8.png"
                ]
            }
        ]

        for item in products:
            product = Product(
                name=item["name"],
                category=item["category"],
                price=item["price"],
                old_price=item["old_price"],
                image=item["image"],
                label=item["label"],
                rating=item["rating"],
                description=item["description"],
                stock=item["stock"],
                is_new_arrival=item["is_new_arrival"],
                is_featured=item["is_featured"],
                is_top_selling=item["is_top_selling"]
            )

            # Attach multiple images
            product.images = [
                ProductImage(image_url=img_path) for img_path in item["images"]
            ]

            db.session.add(product)

        # Seed a sample user
        if Users.query.count() == 0:
            hashed_password = generate_password_hash("password", method='pbkdf2:sha256', salt_length=8)
            sample_user = Users(
                username="Sample User",
                email="sample@example.com",
                password_hash=hashed_password
            )
            db.session.add(sample_user)

        db.session.commit()
        print("Products, images, and sample user seeded successfully!")