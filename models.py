from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    image = db.Column(db.String(200), nullable=False)  # Main image
    label = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Integer, default=4)
    description = db.Column(db.Text, nullable=True)
    stock = db.Column(db.Integer, default=10)

    is_new_arrival = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_top_selling = db.Column(db.Boolean, default=False)

    images = db.relationship("ProductImage", backref="product", lazy=True, cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", lazy=True, cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", lazy=True, cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __repr__(self):
        return f"<ProductImage {self.image_url}>"
    



class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=False, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    cart_items = db.relationship("CartItem", lazy=True, cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"
    

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship("Users")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<CartItem User: {self.user_id}, Product: {self.product_id}, Quantity: {self.quantity}>"


class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    user = db.relationship("Users")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<WishlistItem User: {self.user_id}, Product: {self.product_id}>"