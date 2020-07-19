from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app.recipes.forms import RecipePostForm, SearchForm
from app.models import User, Country, Post
from app.recipes import bp
import os


@bp.route('/country/<country_name>', methods=['GET', 'POST'])
@login_required
def country(country_name):
    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found.'.format(country_name))
        return redirect(url_for('main.index'))

    form = SearchForm()
    already_picked = Post.user_has_post_in_country(current_user.id, country.id)

    if request.method == 'POST':
        button_clicked = request.form.get('submit button')

        if button_clicked == 'select country':
            if not already_picked:
                Post.create_empty_post(country.id)
            return redirect(url_for('recipes.available_posts', country_name='all'))

        if button_clicked == 'search user':
            searched_user = User.get_user_by_username(form.search_user_text.data).first()
            if not searched_user is None:
                return redirect(url_for('recipes.user_country', username=searched_user.username,
                                        country_name=country_name))
            flash('User {} not found'.format(form.search_user_text.data))

        if button_clicked == 'search country':
            searched_country = Country.get_country_by_name(form.search_country_text.data).first()
            if not searched_country is None:
                return redirect(url_for('recipes.country',country_name=searched_country.name))
            flash('Country {} not found'.format(form.search_country_text.data))

    page = request.args.get('page', 1, type=int)
    posts = Post.get_others_posts_by_country_id(country.id).paginate(
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
    search_form = SearchForm()
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
        searched_country = Country.get_country_by_name(search_form.search_country_text.data).first()
        if not searched_country is None:
            return redirect(url_for('recipes.available_posts', country_name=searched_country.name))
        flash('Country {} not found'.format(search_form.search_country_text.data))

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
                           form=form, search_form=search_form, posts=available_posts.items,
                           country_name=country_name.capitalize(),
                           has_data=False, general=general,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/my_posts/<country_name>', methods=['GET', 'POST'])
@login_required
def my_posts(country_name):
    search_form = SearchForm()
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

    if request.method == 'POST' and request.form.get('submit button') == 'search country':
        searched_country = Country.get_country_by_name(search_form.search_country_text.data).first()
        if not searched_country is None:
            return redirect(url_for('recipes.my_posts', country_name=searched_country.name))
        flash('Country {} not found'.format(search_form.search_country_text.data))

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
                           user=current_user, search_form=search_form,
                           posts=posts.items, has_data=True, general=general,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>/country/<country_name>', methods=['GET', 'POST'])
@login_required
def user_country(username, country_name):
    form = SearchForm()

    country = Country.get_country_by_name(country_name).first()
    if country is None:
        flash('Country {} not found.'.format(country_name))
        return redirect(url_for('main.index'))

    user = User.get_user_by_username(username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        button_clicked = request.form.get('submit button')

        if button_clicked == 'search user': 
            searched_user = User.get_user_by_username(form.search_user_text.data).first()
            if not searched_user is None:
                return redirect(url_for('main.user', username=searched_user.username))
            flash('User {} not found'.format(form.search_user_text.data))

        if button_clicked == 'search country':
            searched_country = Country.get_country_by_name(form.search_country_text.data).first()
            if not searched_country is None:
                 return redirect(url_for('recipes.country',country_name=searched_country.name))
            flash('Country {} not found'.format(form.search_country_text.data))
                
    page = request.args.get('page', 1, type=int)
    posts = Post.get_posts_by_user_and_country_ids(user.id, country.id).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes.user_country', username=username, country_name=country_name,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('recipes.user_country', username=username, country_name=country_name,
                       page=posts.prev_num) if posts.has_prev else None

    return render_template('recipes/country.html', title='{}'.format(country_name), 
                            user=user, country=country, form=form, 
                            posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/uploads/post/<post_id>', methods=['GET', 'POST'])
def upload(post_id):
    post = Post.get_post_by_id(post_id).first()
    if post is None:
        flash('Post {} not found.'.format(post.id))
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        allowed_extentions = ['jpeg', 'jpg', 'png']
        path = os.getcwd() + '/app/static/' + post.image_url
        f = request.files.get('file')
        filename = f.filename
        if filename.split('.')[1] in allowed_extentions:
            if os.path.isfile(path):
                os.remove(path)
                post.create_image_url()
                path = os.getcwd() + '/app/static/' + post.image_url
            f.save(path)
            post.set_has_image(True)
            return 'Image updated'

    return 'Nothing to see here' 
