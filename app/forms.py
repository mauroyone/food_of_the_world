from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.get_user_by_username(self.username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.get_user_by_email(self.email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ManipulateTableForm(FlaskForm):
    create = SubmitField('Create')
    pick_country = SubmitField('Of Course!')
    delete = SubmitField('Delete')
    reset = SubmitField('Reset')

class SearchForm(FlaskForm):
    text = StringField('Search text',
        validators=[DataRequired(), Length(min=0, max=40)])
    submit = SubmitField('Search')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = StringField('About me', validators=[Length(min=0, max=140)])
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
    validators=[DataRequired(), Length(min=0, max=32)])
    ingredients = StringField('Recipe ingredients',
        validators=[DataRequired(), Length(min=0, max=1024)])
    steps = StringField('Recipe steps',
        validators=[DataRequired(), Length(min=0, max=4096)])
    country_id = StringField('Country ID', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class SelectCountryForm(FlaskForm):
    select = SubmitField('Give it a try?')
    try_now = SubmitField('Try now!')
