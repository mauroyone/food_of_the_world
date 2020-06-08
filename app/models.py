from app import app, db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from hashlib import md5
from datetime import datetime
from random import randint
from time import time
import jwt

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(64))
    countries = db.relationship('Country', backref='countries', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Country.query.filter_by(available=False).join(
            followers, (followers.c.followed_id == Country.user_id)).filter(
            followers.c.follower_id == self.id).order_by(
            Country.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    @staticmethod
    def get_user_by_username(username):
        user = User.query.filter_by(username=username)
        return user

    @staticmethod
    def get_user_by_email(email):
        user = User.query.filter_by(email=email)
        return user

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    capital = db.Column(db.String(32), index=True)
    flag_url = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    available = db.Column(db.Boolean, index=True, default=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    posts = db.relationship('Post', backref='country_of_origin', lazy='dynamic')
    post_available = db.Column(db.Boolean, index=True, default=False)

    def set_available(self, value):
        self.available = value

    def set_post_available(self, value):
        self.post_available = value

    def set_time(self):
        self.timestamp = datetime.utcnow()
    
    @staticmethod
    def delete_country_table():
        countries = Country.query.filter_by(user_id=current_user.id).all()

        for country in countries:
            db.session.delete(country)
        db.session.commit()

    @staticmethod
    def create_country_table():
        Country.delete_country_table()

        with open('country_list.csv', encoding='utf8') as file:
            for line in file:
                line = line.rstrip()
                line = line.split(',')
                subline = line[0].split(' ')
                for i in range(len(subline)):
                    subline[i] = subline[i].capitalize()

                url = ('https://www.countries-ofthe-world.com/flags-normal/flag-of-' +
                    '-'.join(subline) + '.png')
                country = Country(name=line[0], capital=line[1],
                                    flag_url=url, countries=current_user)
                db.session.add(country)
                db.session.commit()
    
    @staticmethod
    def get_available_country():
        countries = Country.query.filter_by(available=True, user_id=current_user.id).all()
        if countries is None:
            return
        index = randint(0, len(countries)-1)
        countries[index].set_available(False)
        countries[index].set_post_available(True)
        countries[index].set_time()
        db.session.commit()
        return countries[index]

    @staticmethod
    def get_user_used_countries(user):
        countries_used = Country.query.filter_by(available=False, user_id=user.id).order_by(
            Country.timestamp.desc())
        return countries_used
    
    @staticmethod
    def get_available_posts():
        available_posts = Country.query.filter_by(post_available=True,
            user_id=current_user.id).order_by(Country.timestamp.desc())
        return available_posts

    @staticmethod
    def count_available_countries():
        countries = Country.query.filter_by(available=True, user_id=current_user.id).all()
        if countries is None:
            return 0
        return len(countries)

    @staticmethod
    def count_available_posts():
        posts = Country.query.filter_by(post_available=True, user_id=current_user.id).all()
        if posts is None:
            return 0
        return len(posts)

    @staticmethod
    def get_country_by_name(user, name):
        country = Country.query.filter_by(name=name.upper(), user_id=user.id)
        return country

    @staticmethod
    def get_all_used_countries():
        countries = Country.query.filter_by(available=False).order_by(
            Country.timestamp.desc())
        return countries

    def __repr__(self):
        return 'Country {}'.format(self.name)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe = db.Column(db.String(32))
    ingredients = db.Column(db.String(1024))
    steps = db.Column(db.String(4096))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


