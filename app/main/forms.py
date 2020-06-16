from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms.widgets import TextArea
from app.models import User


class IndexForm(FlaskForm):
    pick_country_submit = SubmitField('Wish me luck!')
    search_user_text = StringField('Searching for anybody in particular?',
                                   validators=[Length(min=0, max=40)],
                                   widget=TextArea())
    search_user_submit = SubmitField('Search')
    search_country_text = StringField('Which country are you interested in?',
                                      validators=[Length(min=0, max=40)],
                                      widget=TextArea())
    search_country_submit = SubmitField('Search')
    goto_available_posts_submit = SubmitField('Let\'s go')


class SearchForm(FlaskForm):
    text = StringField('Search text',
                       validators=[DataRequired(), Length(min=0, max=40)])
    submit = SubmitField('Search')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = StringField('About me', validators=[Length(min=0, max=140)],
                           widget=TextArea())
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.get_user_by_username(self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class RecipePostForm(FlaskForm):
    recipe = StringField('Recipe title',
                         validators=[DataRequired(), Length(min=0, max=32)],
                         widget=TextArea())
    ingredients = StringField('Recipe ingredients',
                              validators=[DataRequired(), Length(min=0, max=1024)],
                              widget=TextArea())
    steps = StringField('Recipe steps',
                        validators=[DataRequired(), Length(min=0, max=4096)],
                        widget=TextArea())
    post_id = StringField('Post ID', validators=[DataRequired()])
    submit = SubmitField('Submit')
