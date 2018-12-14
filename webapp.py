import cherrypy
from jinja2 import Environment, PackageLoader, select_autoescape
import os
from datetime import datetime
import sqlite3
import json
from sqlite3 import Error
from models import *


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

    def db_modify_user(db_file,email,password,fullname,address,phone,card):
        db_con = WebApp.db_connection(WebApp.dbsqlite)
        cur = db_con.execute("SELECT * FROM user_db WHERE email == '{}'".format(email))
        row = cur.fetchone()
        password = password if password else row[1]
        fullname = fullname if fullname else row[3]
        address = address if address else row[4]
        phone = phone if phone else row[5]
        card = card if card else row[6]
        new_elem = (email, password, 0, fullname, address, phone, card)
        db_con.execute("DELETE FROM user_db WHERE email == '{}'".format(email))
        db_con.execute("INSERT INTO user_db VALUES {}".format(new_elem))
        db_con.commit()
        db_con.close()

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
            self.set_user(usr)

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
                WebApp.db_modify_user(WebApp.dbsqlite,user['username'],password,fullname,address,phone,card)
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
            #self.do_authenticationJSON(username, password)
            if User[username] != None and User[username].password == password:
                print(username)
                self.set_user(username=username, superuser=User[username].superuser)
            if not self.get_user()['is_authenticated']:
                db_con = WebApp.db_connection(WebApp.dbsqlite)
                sql = "select name from user_db where email == '{}'".format(username)
                cur = db_con.execute(sql)
                row = cur.fetchone()
                tparams = {
                    'title': 'Login',
                    'errors': True,
                    'user': self.get_user(),
                    'year': datetime.now().year,
                }
                return self.render('login.html', tparams)
            else:
                print(self.get_user())
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
    def shop(self):
        tparams = {
            'user': self.get_user(),
            'year': datetime.now().year,
            'products': select(p for p in Product )
        }
        return self.render('shop_navigation.html', tparams)

    @cherrypy.expose
    @db_session
    @cherrypy.tools.json_in()
    def product_management(self):
        user = self.get_user()
        if user['superuser'] == True:
            if cherrypy.request.method == "POST":
                print(cherrypy.request.json)
                dicio = cherrypy.request.json
                if dicio['mode'] == 'update':
                    print('update')
                    product = Product[dicio['id']]
                    product.name = dicio['name']
                    product.weight = dicio['weight']
                elif dicio['mode'] == 'create':
                    print('create')
                    Product(name=dicio['name'], weight=dicio['weight'])
                elif dicio['mode'] == 'delete':
                    print('fdddss')
                    Product[dicio['id']].delete()
                else:
                    pass
            tparams = {
                'user': self.get_user(),
                'year': datetime.now().year,
                'products': select(p for p in Product_Wrapper)
            }
            return self.render('product_management.html', tparams)
        else:
            raise cherrypy.HTTPRedirect("/login")

    @cherrypy.expose
    def shut(self):
        cherrypy.engine.exit()


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    }
    cherrypy.quickstart(WebApp(), '/', conf)
