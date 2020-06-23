from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms.widgets import TextArea, TextInput
from app.models import User


class IndexForm(FlaskForm):
    search_user_text = StringField('Searching for anybody in particular?',
                                   validators=[Length(min=0, max=40)],
                                   widget=TextInput())
    search_country_text = StringField('Which country are you interested in?',
                                      validators=[Length(min=0, max=40)],
                                      widget=TextInput())
    submit = SubmitField('Submit')

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

class FollowForm(FlaskForm):
    submit = SubmitField('Submit')
