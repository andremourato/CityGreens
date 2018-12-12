from pony.orm import *
from datetime import datetime
import sqlite3

pony.options.CUT_TRACEBACK = False
db = Database("sqlite", "data/db.sqlite3", create_db=True)

class User(db.Entity):
    email =  PrimaryKey(str, auto=False)
    password = Required(str)
    name = Required(str)
    address = Required(str)
    phone = Required(str)
    card = Required(str)
    superuser = Required(bool)
    subscription = Optional("Subscription")
    transaction = Optional("Transaction")
    
class Nutritional_Info(db.Entity):
    id = PrimaryKey(int, auto=True)
    product = Required("Product")
    calories, protein, carbohydrates, fat, fibre, salt = [Required(int) for _ in range(6)]

class Product_Wrapper(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    subscription = Set("Subscription")
    transaction = Set("Transaction")

class Product(Product_Wrapper):
    weight = Required(float)
    nutri_info = Optional("Nutritional_Info")
    menu = Set("Menu")

class Menu(Product_Wrapper):
    products = Set("Product")

class Subscription(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    products = Set("Product_Wrapper")

class Transaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    checkout = Required(bool)
    user = Required(User)
    products = Set("Product_Wrapper")
    date = Required(datetime)

db.generate_mapping(create_tables=True)

