from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, TimeField, FloatField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
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
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    admin_tag = BooleanField('IsAdmin?')
    submit = SubmitField('Register')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')


class CreateNewMarketForm(FlaskForm):
    market_name = StringField('Market Name', validators=[DataRequired()])
    market_currency_id = IntegerField('Currency ID', validators=[DataRequired()])
    market_country = StringField('Country', validators=[DataRequired()])
    market_fee = FloatField('Fee', validators=[DataRequired()])
    opens_at = TimeField('Opens At', validators=[DataRequired()])
    closes_at = TimeField('Closes At', validators=[DataRequired()])
    submit = SubmitField('Create New Market')


def validate_username(self, username):
    user = User.query.filter_by(username=username.data).first()
    if user is not None:
        raise ValidationError('Please use a different username.')


def validate_email(self, email):
    mail = User.query.filter_by(email=email.data).first()
    if mail is not None:
        raise ValidationError('Please use a different email adress.')
