from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app.recipes.forms import RecipePostForm, SearchForm
from app.models import User, Country, Post
from app.recipes import bp


@bp.route('/country/<country_name>', methods=['GET', 'POST'])
@login_required
def country(country_name):
    form = SearchForm()

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found.'.format(country_name))
        return redirect(url_for('main.index'))

    already_picked = Post.user_has_post_in_country(current_user.id, country.id)

    if form.validate():
        button_clicked = request.form.get('submit button')
        form_data = form.search_text.data

        if request.method == 'POST' and button_clicked == 'select country':
            return redirect(url_for('recipes.available_posts', country_name='all'))
        if request.method == 'POST' and button_clicked == 'search user':
            user = User.get_user_by_username(form_data).first()
            if user is None:
                flash('User {} not found.'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country_name))
            return redirect(url_for('recipes.country', country_name=country_name))

        if request.method == 'POST' and button_clicked == 'search country':
            country = Country.get_country_by_name(form_data).first()
            if country is None:
                flash('Country {} not found.'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country_name))
            return redirect(url_for('recipes.country',country_name=form_data))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_country_id(country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.country_by_user', country_name=country_name, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.country_by_user', country_name=country_name, page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('recipes/country.html', title='{}'.format(country_name), 
                            country=country, form=form, already_picked=already_picked,
                            posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/available_posts/<country_name>', methods=['GET', 'POST'])
@login_required
def available_posts(country_name):
    search_country_form = SearchForm()
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    if country_name == 'all':
        available_posts = Post.get_my_available_posts().paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
        general = True
    else:
        country = Country.get_country_by_name(country_name).first()
        if country is None:
            flash('Country {} not found'.format(country_name))
            return redirect(url_for('main.index'))
        available_posts = Post.get_my_available_posts_by_country_id(country.id).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
        general = False

    next_url = url_for('recipes.available_posts', country_name=country_name,
                       page=available_posts.next_num) if available_posts.has_next else None
    prev_url = url_for('recipes.available_posts', country_name=country_name,
                       page=available_posts.prev_num) if available_posts.has_prev else None

    if request.method == 'POST' and request.form.get('submit button') == 'search country':
        form_data = search_country_form.search_text.data
        country = Country.get_country_by_name(form_data).first()
        if country is None:
            flash('Country {} not found'.format(form_data))
            return redirect(url_for('recipes.available_posts', country_name=country_name))
        return redirect(url_for('recipes.available_posts', country_name=form_data))

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An unhandled error pop up')
            return redirect(url_for('main.index'))
        post.submit(recipe=form.recipe.data, ingredients=form.ingredients.data,
                    steps=form.steps.data)
        flash('Your post is now alive!')
        return redirect(url_for('recipes.my_posts', country_name='all'))

    return render_template('recipes/my_posts.html', title='Available posts',
                           form=form, search_country_form=search_country_form,
                           posts=available_posts.items, has_data=False, general=general,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/my_posts/<country_name>', methods=['GET', 'POST'])
@login_required
def my_posts(country_name):
    search_country_form = SearchForm()
    form = RecipePostForm()

    page = request.args.get('page', 1, type=int)
    if country_name == 'all':
        posts = Post.get_posts_by_user_id(current_user.id).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
        general = True
    else:
        country = Country.get_country_by_name(country_name).first()
        posts = Post.get_posts_by_user_and_country_ids(current_user.id, country.id).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
        general = False
    next_url = url_for('recipes.my_posts', country_name=country_name, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.my_posts', country_name=country_name, page=posts.prev_num) \
        if posts.has_prev else None

    if request.form.get('submit button') == 'search country':
        form_data = search_country_form.search_text.data
        country = Country.get_country_by_name(form_data).first()
        if country is None:
            flash('Country {} not found'.format(form_data))
            return redirect(url_for('recipes.my_posts', country_name=country_name))
        return redirect(url_for('recipes.my_posts', country_name=form_data))

    if form.validate_on_submit():
        post = Post.get_post_by_id(form.post_id.data).first()
        if post is None:
            flash('An error!')

        if not post.edit(form.recipe.data, form.ingredients.data, form.steps.data):
            flash('No changes were made. Nothing to update')
        else:
            flash('Your post was updated')
            return redirect(url_for('recipes.my_posts', country_name='all'))

    return render_template('recipes/my_posts.html', title='My creations', form=form,
                           user=current_user, search_country_form=search_country_form,
                           posts=posts.items, has_data=True, general=general,
                           next_url=next_url, prev_url=prev_url)

'''
@bp.route('user/<username>/country/<country_name>', methods=['GET', 'POST'])
@login_required
def user_country(username, country_name):
    form = SearchForm()

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found.'.format(country_name))
        return redirect(url_for('main.index'))

    already_picked = Post.user_has_post_in_country(current_user.id, country.id)

    if form.validate():
        button_clicked = request.form.get('submit button')
        form_data = form.search_text.data

        if request.method == 'POST' and button_clicked == 'select country':
            return redirect(url_for('recipes.available_posts', country_name='all'))
        if request.method == 'POST' and button_clicked == 'search user':
            user = User.get_user_by_username(form_data).first()
            if user is None:
                flash('User {} not found.'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country_name))
            return redirect(url_for('recipes.country', country_name=country_name))

        if request.method == 'POST' and button_clicked == 'search country':
            country = Country.get_country_by_name(form_data).first()
            if country is None:
                flash('Country {} not found.'.format(form_data))
                return redirect(url_for('recipes.country', country_name=country_name))
            return redirect(url_for('recipes.country',country_name=form_data))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_country_id(country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.country_by_user', country_name=country_name, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('recipes.country_by_user', country_name=country_name, page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('recipes/country.html', title='{}'.format(country_name), 
                            country=country, form=form, already_picked=already_picked,
                            posts=posts.items, next_url=next_url, prev_url=prev_url)
'''