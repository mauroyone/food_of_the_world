from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    available_countries = db.relationship('AvailableCountries', backref='available', lazy='dynamic')
    used_countries = db.relationship('UsedCountries', backref='used', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username) 


class AvailableCountries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(32), index=True, unique=True)
    capital = db.Column(db.String(32), index=True)
    flag_url = db.Column(db.String(120), index=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return 'Country {}'.format(self.country)


class UsedCountries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(32), index=True, unique=True)
    capital = db.Column(db.String(32), index=True)
    flag_url = db.Column(db.String(120), index=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return 'Country {}'.format(self.country)


