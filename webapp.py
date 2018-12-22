import cherrypy
from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import datetime
import sqlite3
import json
from sqlite3 import Error
from models import *
import os
import io
import base64

class WebApp(object):
    dbsqlite = 'data/db.sqlite3'
    dbjson = 'data/db.json'

    def __init__(self):
        self.env = Environment(
                loader=PackageLoader('webapp', 'templates'),
                autoescape=select_autoescape(['html', 'xml'])
                )


    '''
    Utilities
    '''
    def set_user(self, username=None, superuser=False):
        if username == None:
            cherrypy.session['user'] = {'is_authenticated': False, 'username': ''}
        else:
            cherrypy.session['user'] = {'is_authenticated': True, 'username': username, 'superuser': superuser}


    def get_user(self):
        if not 'user' in cherrypy.session:
            self.set_user()
        return cherrypy.session['user']

    def render(self, tpg, tps):
        template = self.env.get_template(tpg)
        return template.render(tps)

    def db_add_user(db_file, email, password, fullname, address, phone, card):
        db_con = WebApp.db_connection(WebApp.dbsqlite)
        cur = db_con.execute("INSERT INTO user_db VALUES ('{}','{}','{}','{}','{}','{}','{}')".format(email,password,0,fullname,address,phone,card))
        db_con.commit()
        db_con.close()

    @db_session
    def db_get_user(db_file,user):
        print(user)
        user = User[user['username']]
        print(user)
        if user:
            user_info = {
                'email' : user.email,
                'password' : user.password,
                'fullname' : user.name,
                'address'  : user.address,
                'phone'    : user.phone,
                'card'     : user.card,
            }
        return user_info
    
    @db_session
    def db_modify_user(email,password,fullname,address,phone,card):
        user = User.get(email=email)
        user.password = password if password else user.password
        user.name = fullname if fullname else user.name
        user.address = address if address else user.address
        user.phone = phone if phone else user.phone
        user.card = card if card else user.card
        commit()

    def db_connection(db_file):
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return None

    @db_session
    def do_authenticationDB(self, usr, pwd):
        user = self.get_user()
        row = User.get(email=usr, password=pwd)
        if row != None:
            self.set_user(usr, row.superuser)

    '''
    Controllers
    '''
    @cherrypy.expose
    def index(self):
        tparams = {
            'user': self.get_user(),
            'year': datetime.now().year,
        }
        return self.render('index.html', tparams)

    @cherrypy.expose
    def user_homepage(self,password=None,fullname=None,address=None,phone=None,card=None):
        user = self.get_user()
        # User must be authenticated before accessing the user homepage
        if user['is_authenticated']:
            if password or fullname or address or phone or card:
                print(fullname)
                WebApp.db_modify_user(user['username'],password,fullname,address,phone,card)
            db_info = self.db_get_user(user)
            tparams = {
                'user' : user,
                'email' : db_info['email'],
                'password' : db_info['password'],
                'fullname' : db_info['fullname'],
                'address' : db_info['address'],
                'phone' : db_info['phone'],
                'card'  : db_info['card']
            }
            return self.render('user_homepage.html',tparams)
        else:
            raise cherrypy.HTTPRedirect("/login")

    @cherrypy.expose
    @db_session
    def login(self, username=None, password=None):
        if username == None:
            tparams = {
                'title': 'Login',
                'errors': False,
                'user': self.get_user(),
                'year': datetime.now().year,
            }
            return self.render('login.html', tparams)
        else:
            self.do_authenticationDB(username, password)
            if not self.get_user()['is_authenticated']:
                tparams = {
                    'title': 'Login',
                    'errors': True,
                    'user': self.get_user(),
                    'year': datetime.now().year,
                }
                return self.render('login.html', tparams)
            else:
                raise cherrypy.HTTPRedirect("/user_homepage")

    @cherrypy.expose
    @db_session
    def signup(self, email=None, password=None, fullname=None, address=None, phone=None, card=None):
        tparams = {'user' : self.get_user()}
        if email != None and password != None and fullname != None and address != None and phone != None and card != None:
            if len(email) != 0 and len(password) != 0 and len(fullname) != 0 and len(address) != 0 and len(phone) != 0 and len(card) != 0:
                User(email=email, password=password, name=fullname, address=address, phone=phone, card=card, superuser=False)
            tparams = {
                'user' : self.get_user(),
                'email' : len(email),
                'password' : len(password),
                'fullname' : len(fullname),
                'address' : len(address),
                'phone' : len(phone),
                'card' : len(card)
            }
        return self.render('signup.html',tparams)

    @cherrypy.expose
    def about(self):
        tparams = {
            'title': 'About',
            'message': 'Your application description page.',
            'user': self.get_user(),
            'year': datetime.now().year,
        }
        return self.render('about.html', tparams)


    @cherrypy.expose
    def contact(self):
        tparams = {
            'title': 'Contact',
            'message': 'Your contact page.',
            'user': self.get_user(),
            'year': datetime.now().year,
        }
        return self.render('contact.html', tparams)

    @cherrypy.expose
    def logout(self):
        self.set_user()
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    @db_session
    def shop(self, add2cart=None):
        user = self.get_user()
        number = 0
        if user['username']:
            t = Transaction.get(user=User[user['username']], checkout=False)
            items = 0
            if cherrypy.request.method == "POST":
                if t == None:
                    t = Transaction(checkout=False, user=User[user['username']], date=datetime.now(), products={str(add2cart): 1})
                    commit()

                elif str(add2cart) not in t.products.keys():
                    t.products[str(add2cart)] = 1
                    commit()
                else:
                    t.products[str(add2cart)] += 1
                    commit()
            
            if t == None:
                items = 0
            else:
                for v in t.products.values():
                    items += int(v)
            tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': select(p for p in Product),
                'menus': select(m for m in Menu),
                'items': items
            }
        else:
            tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': select(p for p in Product),
                'menus': select(m for m in Menu)
            }
        return self.render('shop_navigation.html', tparams)

    @cherrypy.expose
    def admin(self, **kwargs):
        tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
            }
        return self.render('admin.html', tparams)


    @cherrypy.expose
    @db_session
    def product_management(self, **kwargs):
        user = self.get_user()
        #aceder aos campos name do html
        params = cherrypy.request.body.params
        if user['superuser'] == True:
            if cherrypy.request.method == "POST":
                if 'update' in params:
                    product = Product[params['id']]
                    product.name = params['name']
                    product.weight = params['weight']
                    product.price = params['price']
                    product.description = params['description']
                    if params['image'].file is not None:
                        self.image_wrapper(params['id'], params['image'])
                    else:
                        pass
                elif 'delete' in params:
                    Product[params['id']].delete()
                    self.image_wrapper(params['id'], params['image'], delete=True)
                elif 'add' in params:
                    p = Product(name=params['name'], weight=params['weight'], price=params['price'], description=params['description'])
                    commit()
                    self.image_wrapper(p.id, params['image'])

            tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': select(p for p in Product),
            }
            return self.render('product_management.html', tparams)
        else:
            raise cherrypy.HTTPRedirect("/user_homepage")
    
    @cherrypy.expose
    @db_session
    def menu_management(self, **kwargs):
        user = self.get_user()
        #aceder aos campos name do html
        params = cherrypy.request.body.params
        if user['superuser'] == True:
            if cherrypy.request.method == "POST":
                if 'update' in params:
                    menu = Menu[params['id']]
                    menu.name = params['name']
                    menu.price = params['price']
                    menu.description = params['description']
                    if params['image'].file is not None:
                        self.image_wrapper(params['id'], params['image'])
                    else:
                        pass
                elif 'delete' in params:
                    Product[params['id']].delete()
                    self.image_wrapper(params['id'], params['image'], delete=True)
                elif 'add' in params:
                    m = Menu(name=params['name'], price=params['price'], description=params['description'])
                    commit()
                    self.image_wrapper(m.id, params['image'])

            tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': select(m for m in Menu),
            }
            return self.render('menu_management.html', tparams)
        else:
            raise cherrypy.HTTPRedirect("/user_homepage")

    @cherrypy.expose
    @db_session
    def cart(self, **kwargs):
        user = self.get_user()
        products = None
        if user['username']:
            t = Transaction.get(user=User[user['username']], checkout=False)
            if cherrypy.request.method == 'POST':
                if 'delete' in kwargs:
                    print(kwargs['delete'])
                    t.products.pop(kwargs['delete'])
                    commit()
                elif 'update' in kwargs:
                    t.products[str(kwargs['update'])] = int(kwargs['quantity'])
                    commit()

            if t != None:
                quantity = dict(t.products)
                products = select(p for p in Product)
                l2 = [{'id': p.id, 'name': p.name, 'price': p.price, 'quantity': quantity[str(p.id)]} for p in products if str(p.id) in quantity]
            else:
                l2 = []
            tparams = {
                'title': 'Cart',
                'message': 'Your cart page.',
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': l2
            }
        return self.render('cart.html', tparams)
    

    @cherrypy.expose
    def shut(self):
        cherrypy.engine.exit()

    def image_wrapper(self, id, image, delete=False):
        fn = os.path.join(os.path.dirname(__file__), "data/img/" + str(id) + ".jpg")
        if delete:
            os.remove(fn)
        else:
            file1 = io.BytesIO(image.file.read())
            myFile = open(fn, 'wb')
            myFile.write(file1.read1())
            myFile.close()

if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        },
        '/img': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './data/img'
        }
    }
    '''
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 80,
        'environment': 'production'
    })
    '''
    cherrypy.quickstart(WebApp(), '/', conf)
