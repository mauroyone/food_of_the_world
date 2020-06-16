from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app.recipes.forms import SelectCountryForm, RecipePostForm
from app.models import User, Country, Post
from app.recipes import bp


@bp.route('/user/<username>/country/<country>', methods=['GET', 'POST'])
@login_required
def country(username, country):
    form = SelectCountryForm()

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))

    searched_country = Country.get_country_by_name(country).first()
    if searched_country is None:
        flash('Country {} not found.'.format(country))
        return redirect(url_for('main.index'))

    post = Post.get_my_post_by_country(searched_country.id).first()
    try_now = False if post is None else True

    if form.submit.data:
        if not try_now:
            Post.create_empty_post(searched_country.id)
            flash('manual selection')
        return redirect(url_for('recipes.available_posts'))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_country_id(searched_country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.country', username=username, country=country, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.country', username=username, country=country, page=posts.prev_num) \
        if posts.has_prev else None


    return render_template('recipes/country.html', title='Your country', posts=posts.items,
                           country=searched_country, user=user, form=form,
                           next_url=next_url, prev_url=prev_url, try_now=try_now)

@bp.route('/available_posts', methods=['GET', 'POST'])
@login_required
def available_posts():
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    available_posts = Post.get_my_available_posts().paginate(
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
        return redirect(url_for('main.index'))

    return render_template('recipes/my_posts.html', title='Available posts',
                           form=form, posts=available_posts.items,
                           next_url=next_url, prev_url=prev_url, has_data=False)

@bp.route('/my_posts', methods=['GET', 'POST'])
@login_required
def my_posts():
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user(current_user).paginate(
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
            return redirect(url_for('main.index'))

    return render_template('recipes/my_posts.html', title='My creations', form=form,
                           user=current_user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, has_data=True)
