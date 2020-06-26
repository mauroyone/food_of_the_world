from random import randint
from time import time
from datetime import datetime
from hashlib import md5
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin, current_user
from app import db, login

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(64))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
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
        return Post.query.join(followers,
                               (followers.c.followed_id == Post.user_id)).filter(
                                   followers.c.follower_id == self.id,
                                   Post.submitted == True).order_by(
                                       Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

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
        return User.query.filter_by(username=username.capitalize())

    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email)

    def __repr__(self):
        return '<User {}\nId {}>'.format(self.username, self.id)


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    capital = db.Column(db.String(32), index=True)
    flag_url = db.Column(db.String(128), index=True)
    posts = db.relationship('Post', backref='origin', lazy='dynamic')

    @staticmethod
    def delete_country_table():
        countries = Country.query.all()
        for country in countries:
            db.session.delete(country)
        db.session.commit()

    @staticmethod
    def create_country_table():

        with open('country_list.csv', encoding='utf8') as file:
            for line in file:
                line = line.rstrip()
                line = line.split(',')
                url = line[2] + ' - flag.jpg'
                country = Country(name=line[0].upper(), capital=line[1],
                                  flag_url=url)
                db.session.add(country)
            db.session.commit()

    @staticmethod
    def get_country_by_name(name):
        return Country.query.filter_by(name=name.upper())

    @staticmethod
    def get_all_countries():
        return Country.query.order_by(Country.name)

    @staticmethod
    def get_random_country(picked_countries):
        available_countries = Country.query.filter(
            ~Country.id.in_(picked_countries)).all()
        index = randint(0, len(available_countries)-1)
        return available_countries[index]

    @staticmethod
    def count_countries():
        return len(Country.query.all())

    def __repr__(self):
        return 'Country: {}\nCapital: {}\n URL: {}\n'.format(self.name, self.capital,
                                                             self.flag_url)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe = db.Column(db.String(32), default='')
    ingredients = db.Column(db.String(1024), default='')
    steps = db.Column(db.String(4096), default='')
    submitted = db.Column(db.Boolean, index=True, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    image_url = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))

    def set_submitted(self, value):
        self.submitted = value

    def submit(self, recipe, ingredients, steps):
        self.recipe = recipe
        self.ingredients = ingredients
        self.steps = steps
        self.submitted = True
        self.timestamp = datetime.utcnow()

        db.session.add(self)
        db.session.commit()

    def edit(self, recipe, ingredients, steps):
        if (self.recipe == recipe and self.ingredients == ingredients
                and self.steps == steps):
            return None
        self.recipe = recipe
        self.ingredients = ingredients
        self.steps = steps
        self.timestamp = datetime.utcnow()
        db.session.commit()
        return 1

    @staticmethod
    def create_empty_post(country_id):
        post = Post(user_id=current_user.id, country_id=country_id)
        db.session.add(post)
        db.session.commit()

    @staticmethod
    def delete_posts():
        posts = Post.query.filter_by(user_id=current_user.id).all()
        for post in posts:
            db.session.delete(post)
        db.session.commit()

    @staticmethod
    def get_post_by_id(id):
        return Post.query.filter_by(id=id)

    @staticmethod
    def get_all_submitted_posts():
        return Post.query.filter_by(submitted=True).order_by(Post.timestamp.desc())

    @staticmethod
    def get_posts_by_country_id(country_id):
        return Post.query.filter_by(submitted=True, country_id=country_id).order_by(
            Post.timestamp.desc())

    @staticmethod
    def get_posts_by_user_id(user_id):
        return Post.query.filter_by(submitted=True, user_id=user_id).order_by(
            Post.timestamp.desc())

    @staticmethod
    def get_my_available_posts():
        return Post.query.filter_by(submitted=False,
                                    user_id=current_user.id).order_by(
                                        Post.timestamp.desc())
    
    @staticmethod
    def get_my_available_posts_by_country_id(country_id):
        return Post.query.filter_by(submitted=False, country_id=country_id,
                                    user_id=current_user.id).order_by(
                                        Post.timestamp.desc())

    @staticmethod
    def get_my_countries_with_posts():
        countries_with_posts = Post.query.filter_by(user_id=current_user.id).all()
        return [picked_country.id for picked_country in countries_with_posts]

    @staticmethod
    def get_others_posts_by_country_id(country_id):
        return Post.query.filter(Post.submitted).filter(
            Post.user_id != current_user.id).filter(
                Post.country_id == country_id).order_by(Post.timestamp.desc())

    @staticmethod
    def get_posts_by_user_and_country_ids(user_id, country_id):
        return Post.query.filter_by(submitted=True, user_id=user_id,
                                    country_id=country_id).order_by(Post.timestamp.desc())

    @staticmethod
    def user_has_post_in_country(user_id, country_id):
        return not (Post.query.filter_by(user_id=user_id, country_id=country_id).first() is None)

    @staticmethod
    def count_different_countries_with_posts():
        different_countries = Post.query.filter_by(
            user_id=current_user.id).distinct().all()
        if different_countries is None:
            return 0
        return len(different_countries)

    @staticmethod
    def count_available_posts():
        available_posts = Post.query.filter_by(submitted=False,
                                               user_id=current_user.id).all()
        if available_posts is None:
            return 0
        return len(available_posts)

    def __repr__(self):
        return 'Author: {}\nCountry: {}\nRecipe: {}\n'.format(self.user_id,
                                                              self.country_id,
                                                              self.recipe)
