import cherrypy
from jinja2 import Environment, PackageLoader, select_autoescape
import os
from datetime import datetime
import sqlite3
from sqlite3 import Error
import json


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
    def set_user(self, username=None):
        if username == None:
            cherrypy.session['user'] = {'is_authenticated': False, 'username': ''}
        else:
            cherrypy.session['user'] = {'is_authenticated': True, 'username': username}


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

    def db_get_user(db_file,user):
        db_con = WebApp.db_connection(WebApp.dbsqlite)
        cur = db_con.execute("SELECT * FROM user_db WHERE email == '{}'".format(user['username']))
        row = cur.fetchone()
        db_con.close()
        user_info = {
            'email' : row[0],
            'password' : row[1],
            'fullname' : row[3],
            'address'  : row[4],
            'phone'    : row[5],
            'card'     : row[6]
        }
        return user_info

    def db_connection(db_file):
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return None


    def do_authenticationDB(self, usr, pwd):
        user = self.get_user()
        db_con = WebApp.db_connection(WebApp.dbsqlite)
        sql = "select * from user_db where email == '{}'".format(usr)
        cur = db_con.execute(sql)
        row = cur.fetchone()
        if row != None:
            if row[1] == pwd:
                self.set_user(usr)

        db_con.close()


    def do_authenticationJSON(self, usr, pwd):
        user = self.get_user()
        db_json = json.load(open(WebApp.dbjson))
        users = db_json['users']
        for u in users:
            if u['username'] == usr and u['password'] == pwd:
                self.set_user(usr)
                break

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
    def user_homepage(self):
        user = self.get_user()
        # User must be authenticated before accessing the user homepage
        if user['is_authenticated']:
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
            self.do_authenticationDB(username, password)
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
                raise cherrypy.HTTPRedirect("/user_homepage")

    @cherrypy.expose
    def signup(self, email=None, password=None, fullname=None, address=None, phone=None, card=None):
        tparams = {'user' : self.get_user()}
        if email != None and password != None and fullname != None and address != None and phone != None and card != None:
            if len(email) != 0 and len(password) != 0 and len(fullname) != 0 and len(address) != 0 and len(phone) != 0 and len(card) != 0:
                WebApp.db_add_user(WebApp.dbsqlite, email, password, fullname, address, phone, card)
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
    def shop(self):
        tparams = {
            'user': self.get_user(),
            'year': datetime.now().year,
        }
        return self.render('shop_navigation.html', tparams)


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
