from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms.widgets import TextArea


class SearchForm(FlaskForm):
    search_user_text = StringField('Searching for anybody in particular?',
                                   validators=[DataRequired(), Length(min=0, max=40)])
    search_country_text = StringField('Which country are you interested in?',
                                      validators=[DataRequired(), Length(min=0, max=40)])
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
