from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app import db
from app.main.forms import IndexForm, EditProfileForm, FollowForm
from app.models import User, Country, Post
from app.main import bp


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = IndexForm()

    amount_of_available_countries = (Country.count_countries() -
                                     Post.count_different_countries_with_posts())
    amount_of_available_posts = Post.count_available_posts()

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    
    if request.method == 'POST':
        button_clicked = request.form.get('submit button')
        
        if button_clicked == 'go to available posts':
            return redirect(url_for('recipes.available_posts'))

        if button_clicked == 'pick country':
            if amount_of_available_countries == 0:
                flash('You don\'t have any left country to try.')
                flash('Please search for that country you really want' +
                    'o give another try.')
                flash('Or, if you are brave enough, reset the whole list!')
                return redirect(url_for('main.user', username=current_user.username))
            picked_countries = Post.get_my_countries_with_posts()
            country = Country.get_random_country(picked_countries)
            Post.create_empty_post(country.id)
            return redirect(url_for('recipes.country', country_name=country.name))

        if button_clicked == 'search user':    
            form_data = form.search_user_text.data
            user = User.get_user_by_username(form_data).first()
            if user is None:
                flash('User {} not found'.format(form_data))
                return redirect(url_for('main.index'))
            else:
                flash('Yeah! you searched for {}'.format(form_data))
                return redirect(url_for('main.user', username=user.username))

        if button_clicked == 'search country':
            form_data = form.search_country_text.data
            country = Country.get_country_by_name(form_data).first()
            if country is None:
                flash('Country {} not found'.format(form_data))
                return redirect(url_for('main.index'))
            else:
                flash('Yeah! you searched for {}'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country.name))

    return render_template('index.html', title='Home', index=True, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form,
                           amount_of_available_countries=amount_of_available_countries,
                           amount_of_available_posts=amount_of_available_posts)

@bp.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form = IndexForm()

    page = request.args.get('page', 1, type=int)
    posts = Post.get_all_submitted_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None

    if request.method == 'POST':
        button_clicked = request.form.get('submit button')

        if button_clicked == 'search user':    
            form_data = form.search_user_text.data
            user = User.get_user_by_username(form_data).first()
            if user is None:
                flash('User {} not found'.format(form_data))
                return redirect(url_for('main.index'))
            else:
                flash('Yeah! you searched for {}'.format(form_data))
                return redirect(url_for('main.user', username=user.username))

        if button_clicked == 'search country':
            form_data = form.search_country_text.data
            country = Country.get_country_by_name(form_data).first()
            if country is None:
                flash('Country {} not found'.format(form_data))
                return redirect(url_for('main.index'))
            else:
                flash('Yeah! you searched for {}'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country.name))

    return render_template('index.html', title='Explore', posts=posts.items,
                           form=form, next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = FollowForm()

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user_id(user.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None

    if form.validate_on_submit():
        Post.delete_posts()
        return redirect(url_for('main.index'))

    return render_template('user.html', user=user, posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.get_user_by_username(username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.get_user_by_username(username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.explore', username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/flags')
@login_required
def flags():
    countries = Country.get_all_countries()
    return render_template('flags.html', countries=countries)
