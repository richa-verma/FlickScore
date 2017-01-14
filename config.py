from pymongo import MongoClient

WTF_CSRF_ENABLED = True
SECRET_KEY = 'Put your secret key here'
DB_NAME = 'imdb'

DATABASE = MongoClient()[DB_NAME]
POSTS_COLLECTION = DATABASE.movies
USERS_COLLECTION = DATABASE.users
SETTINGS_COLLECTION = DATABASE.settings

DEBUG = True

GOOGLE_LOGIN_CLIENT_ID = '250725106235-un9ngj4hdrgf3peobeu2dgvl8np7slrc.apps.googleusercontent.com'
GOOGLE_LOGIN_CLIENT_SECRET = 'OeVpn-mi_5x7-OH1Rec7YyUk'

OAUTH_CREDENTIALS={
        'google': {
            'id': GOOGLE_LOGIN_CLIENT_ID,
            'secret': GOOGLE_LOGIN_CLIENT_SECRET
        }
}