from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, CreateNewMarketForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from app.models import User, Post, Market
from flask_login import login_required
from werkzeug.urls import url_parse
from datetime import datetime


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required  # nur sichtbar für eingeloggte User
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = Post.query.all()
    markets = Market.query.all()
    return render_template('index.html', title='Home', form=form, posts=posts, markets=markets)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # is_authenticated is true if user has valid credentials or false otherwise
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # mit query.filter wird die User datenbank nach dem User untersucht
        # .first() liefert das erste Ergebnis es gibt hier ja nur eines,
        # .all() würde eine Liste liefern
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/createmarket', methods=['GET', 'POST'])
def createmarket():
    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))
    form = CreateNewMarketForm()
    if form.validate_on_submit():
        market = Market(market_name=form.market_name.data, opens_at=form.opens_at.data, closes_at=form.closes_at.data,
                        market_currency_id=form.market_currency_id.data, market_country=form.market_country.data,
                        market_fee=form.market_fee.data)
        db.session.add(market)
        db.session.commit()
        flash('New market has been created!')
        return redirect(url_for('index'))
    return render_template('create_market.html', title='Create Market', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.all()
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        return render_template('edit_profile.html', title='Edit Profile', form=form)
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

