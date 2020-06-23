from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app.recipes.forms import SelectCountryForm, RecipePostForm
from app.models import User, Country, Post
from app.recipes import bp


@bp.route('/user/<username>/country/<country_name>', methods=['GET', 'POST'])
@login_required
def country(username, country_name):
    form = SelectCountryForm()

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found.'.format(country_name))
        return redirect(url_for('main.index'))

    post = Post.get_posts_by_user_country(user.id, country.id).first()
    try_now = False if post is None else True

    if form.submit.data:
        if not try_now:
            Post.create_empty_post(country.id)
            flash('manual selection')
        return redirect(url_for('recipes.available_posts'))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_country_id(country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.country', username=username, country=country, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.country', username=username, country=country, page=posts.prev_num) \
        if posts.has_prev else None


    return render_template('recipes/country.html', title='Your country', posts=posts.items,
                           country=country, user=user, form=form,
                           next_url=next_url, prev_url=prev_url, try_now=try_now)

@bp.route('/available_posts', methods=['GET', 'POST'])
@login_required
def available_posts():
    search_country_form = SelectCountryForm()
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    available_posts = Post.get_my_available_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.available_posts', page=available_posts.next_num) \
        if available_posts.has_next else None
    prev_url = url_for('recipes.available_posts', page=available_posts.prev_num) \
        if available_posts.has_prev else None

    if request.form.get('submit button') == 'search country':
        form_data = search_country_form.search_country_text.data
        country = Country.get_country_by_name(form_data).first()
        if country is None:
            flash('Country {} not found'.format(form_data))
            return redirect(url_for('recipes.available_posts'))
        return redirect(url_for('recipes.available_posts_by_country', country_name=form_data))

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An unhandled error pop up')
            return redirect(url_for('main.index'))
        post.submit(recipe=form.recipe.data, ingredients=form.ingredients.data,
                    steps=form.steps.data)
        flash('Your post is now alive!')
        return redirect(url_for('recipes.my_posts'))

    return render_template('recipes/my_posts.html', title='Available posts',
                           form=form, search_country_form=search_country_form,
                           posts=available_posts.items,
                           next_url=next_url, prev_url=prev_url, has_data=False)

@bp.route('/available_posts/country/<country_name>', methods=['GET', 'POST'])
@login_required
def available_posts_by_country(country_name):
    form = RecipePostForm()

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found'.format(country_name))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    available_posts = Post.get_my_available_posts_by_country(country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.available_posts', page=available_posts.next_num) \
        if available_posts.has_next else None
    prev_url = url_for('recipes.available_posts', page=available_posts.prev_num) \
        if available_posts.has_prev else None

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An unhandled error pop up')
            return redirect(url_for('main.index'))
        post.submit(recipe=form.recipe.data, ingredients=form.ingredients.data,
                    steps=form.steps.data)
        flash('Your post is now alive!')
        return redirect(url_for('recipes.my_posts'))
    return render_template('recipes/my_posts.html', title='Available posts',
                           form=form, posts=available_posts.items,
                           next_url=next_url, prev_url=prev_url, has_data=False)

@bp.route('/my_posts', methods=['GET', 'POST'])
@login_required
def my_posts():
    search_country_form = SelectCountryForm()
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user(current_user).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.my_posts', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.my_posts', page=posts.prev_num) \
        if posts.has_prev else None

    if request.form.get('submit button') == 'search country':
        form_data = search_country_form.search_country_text.data
        country = Country.get_country_by_name(form_data).first()
        if country is None:
            flash('Country {} not found'.format(form_data))
            return redirect(url_for('recipes.my_posts'))
        return redirect(url_for('recipes.my_posts_by_country', country_name=form_data))

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An error!')

        if not post.edit(form.recipe.data, form.ingredients.data, form.steps.data):
            flash('No changes were made. Nothing to update')
        else:
            flash('Your post was updated')
            return redirect(url_for('recipes.my_posts'))

    return render_template('recipes/my_posts.html', title='My creations', form=form,
                           user=current_user, search_country_form=search_country_form,
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           has_data=True)

@bp.route('/my_posts/country/<country_name>', methods=['GET', 'POST'])
@login_required
def my_posts_by_country(country_name):
    form = RecipePostForm()

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found'.format(country_name))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user_country(current_user.id, country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.my_posts', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.my_posts', page=posts.prev_num) \
        if posts.has_prev else None

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An error!')

        if not post.edit(form.recipe.data, form.ingredients.data, form.steps.data):
            flash('No changes were made. Nothing to update')
        else:
            flash('Your post was updated')
            return redirect(url_for('recipes.my_posts'))

    return render_template('recipes/my_posts.html', title='My creations', form=form,
                           user=current_user, posts=posts.items, next_url=next_url, 
                           prev_url=prev_url, has_data=True)