from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Table, Column, String, select, DateTime, Float
from marshmallow import ValidationError
from typing import List, Optional
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Lima22Alpha#@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating our Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

########################################################################################################
# Association Table
Order_Product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("product.id"), primary_key=True)
)

# Models
class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), unique=True, nullable=False)
    #One-to-Many relationship from this User to a List of Order Objects
    orders: Mapped[List["Orders"]] = relationship("Orders", back_populates="user")
    
class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id")) 
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    products: Mapped[List["Product"]] = relationship("Product", secondary=Order_Product, back_populates="orders")
    user = relationship("User", back_populates="orders")

class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    orders: Mapped[List["Orders"]] = relationship("Orders", secondary=Order_Product, back_populates="products")

##############################################################################################################
# Implement Marshmallow schemas 
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    products = ma.Method("get_product_ids")
    class Meta:
        model = Orders
        include_fk = True
    def get_product_ids(self, obj):
        return [p.id for p in obj.products]

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        
user_schema = UserSchema()
users_schema = UserSchema(many=True) #allows for serialization of a list of user objects
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

##############################################################################################################
#User Endpoints

#GET /users: Retrieve all users
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

############################
#GET /users/<id>: Retrieve a user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    user = db.session.get(User, id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return user_schema.jsonify(user), 200

############################
#POST /users: Create a new user
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201    

############################
#PUT /users/<id>: Update a user by ID
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']

    db.session.commit()
    return user_schema.jsonify(user), 200

############################
#DELETE /users/<id>: Delete a user by ID
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "Invalid user id"}), 400 
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"successfully deleted user {id}"}), 200

##############################################################################################################
#Product Endpoints
#GET /products: Retrieve all products
@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products), 200

############################
#GET /products/<id>: Retrieve a product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    product = db.session.get(Product, id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return product_schema.jsonify(product), 200

############################
#POST /products: Create a new product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201    

############################
#PUT /products/<id>: Update a product by ID
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200

############################
#DELETE /products/<id>: Delete a product by ID
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Invalid product id"}), 400 
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"successfully deleted product {id}"}), 200

##############################################################################################################
#Order Endpoints
#POST /orders: Create a new order (requires user ID and order date)
@app.route('/orders', methods=['POST'])
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    user = db.session.get(User, order_data['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    new_order = Orders(user_id=order_data['user_id'], order_date=order_data['order_date'])
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201

############################
#PUT /orders/<order_id>/add_product/<product_id>: Add a product to an order (prevent duplicates)
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Orders, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product in order.products:
        return jsonify({"message": "Product already in order"}), 200
    order.products.append(product)
    db.session.commit()
    return order_schema.jsonify(order), 200

############################
#DELETE /orders/<order_id>/remove_product/<product_id>: Remove a product from an order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def delete_product_from_order(order_id, product_id):
    order = db.session.get(Orders, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    #product = Product.query.get(product_id)
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product not in order.products:
        return jsonify({"message": "Product not in order"}), 200
    order.products.remove(product)
    db.session.commit()
    return order_schema.jsonify(order), 200

############################
#GET /orders/user/<user_id>: Get all orders for a user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_with_userid(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return orders_schema.jsonify(user.orders), 200

############################
#GET /orders/<order_id>/products: Get all products for an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_with_order_id(order_id):
    order = db.session.get(Orders, order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404
    return products_schema.jsonify(order.products), 200
    
##############################################################################################################

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        #db.drop_all()
        
    app.run(debug=True)