from random import randint
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.forms import EmptyForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms import RecipePostForm, IndexForm, SelectCountryForm
from app.models import User, Country, Post
from app.email import send_password_reset_email



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = IndexForm()

    amount_of_available_countries = Country.count_available_countries()
    amount_of_available_posts = Country.count_available_posts()

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None


    if form.pick_country_submit.data:
        if amount_of_available_countries == 0:
            flash('You don\'t have any left country to try.')
            flash('Please search for that country you really want' +
                'o give another try.')
            flash('Or, if you are brave enough, reset the whole list!')
            return redirect(url_for('user', username=current_user.username))

        country = Country.get_available_country()
        return redirect(url_for('country', username=current_user.username,
                                country=country.name))
    if form.search_user_submit.data:
        form_data = form.search_user_text.data
        user = User.get_user_by_username(form_data).first()
        if user is None:
            flash('User {} not found'.format(form_data))
            return redirect(url_for('index'))
        else:
            flash('Yeah! you searched for {}'.format(form_data))
            return redirect(url_for('user', username=user.username))
    if form.search_country_submit.data:
        form_data = form.search_country_text.data
        country = Country.get_country_by_name(current_user, form_data).first()
        if country is None:
            flash('Country {} not found'.format(form_data))
            return redirect(url_for('index'))
        else:
            flash('Yeah! you searched for {}'.format(form_data))
            return redirect(url_for('country', username=current_user.username,
                                    country=country.name))
    if form.goto_available_posts_submit.data:
        return redirect(url_for('available_posts'))

    return render_template('index.html', title='Home', posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form,
                           amount_of_available_countries=amount_of_available_countries,
                           amount_of_available_posts=amount_of_available_posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_user_by_username(form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.get_user_by_email(form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        Country.create_country_table()
        logout_user()
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = EmptyForm()

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user(user).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None

    if form.validate_on_submit():
        Country.create_country_table()
        Post.delete_posts()
        return redirect(url_for('index'))

    return render_template('user.html', user=user, posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.get_user_by_username(username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.get_user_by_username(username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('explore', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.get_all_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/user/<username>/country/<country>', methods=['GET', 'POST'])
@login_required
def country(username, country):
    form = SelectCountryForm()

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    searched_country = Country.get_country_by_name(user, country).first()
    if searched_country is None:
        flash('Country {} not found.'.format(country))
        return redirect(url_for('index'))

    if form.try_now.data:
        flash('try now')
        return redirect(url_for('available_posts'))

    if form.select.data:
        searched_country.set_available(False)
        searched_country.set_post_available(True)
        searched_country.set_time()
        db.session.commit()
        flash('manual selection')
        return redirect(url_for('available_posts'))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_country(searched_country.id).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('country', username=username, country=country, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('country', username=username, country=country, page=posts.prev_num) \
        if posts.has_prev else None


    return render_template('country.html', title='Your country', posts=posts.items,
                           country=searched_country, user=user, form=form,
                           next_url=next_url, prev_url=prev_url)

@app.route('/available_posts', methods=['GET', 'POST'])
@login_required
def available_posts():
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    available_posts = Country.get_countries_with_available_post().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('available_posts', page=available_posts.next_num) \
        if available_posts.has_next else None
    prev_url = url_for('available_posts', page=available_posts.prev_num) \
        if available_posts.has_prev else None

    if form.validate_on_submit():
        country = Country.get_country_by_id(form.country_id.data).first()
        if country is None:
            flash('An unhandled error pop up')
            return redirect(url_for('index'))
        country.set_post_available(False)

        post = Post(recipe=form.recipe.data, ingredients=form.ingredients.data,
                    steps=form.steps.data, user_id=current_user.id,
                    country_id=form.country_id.data)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now alive!')
        return redirect(url_for('index'))

    return render_template('available_posts.html', title='Available posts',
                           form=form, available_posts=available_posts.items,
                           next_url=next_url, prev_url=prev_url,)

@app.route('/my_posts', methods=['GET', 'POST'])
@login_required
def my_posts():
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user(current_user).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('my_posts', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('my_posts', page=posts.prev_num) \
        if posts.has_prev else None

    if form.validate_on_submit():
        Post.post_edit(form.recipe.data, form.ingredients.data, form.steps.data,
                       form.country_id.data)

    return render_template('my_posts.html', title='My creations', form=form,
                           user=current_user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/flags')
@login_required
def flags():
    countries = Country.get_all_countries()
    return render_template('flags.html', countries=countries)