import csv
import io
import json

import pandas as pd
import requests
from sqlalchemy import select, column
from sqlalchemy.orm import query

from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, CreateNewMarketForm
from flask import render_template, flash, redirect, url_for, request, jsonify, Response
from flask_login import current_user, login_user, logout_user
from app.models import User, Post, Market, Transactions, Offer, Currency
from flask_login import login_required
from werkzeug.urls import url_parse
from datetime import datetime

import sqlite3


@app.context_processor
def inject_datetime():
    return {'current_time': datetime.utcnow()}


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required  # nur sichtbar für eingeloggte User
def index():
    # form = PostForm()
    # if form.validate_on_submit():
    #     post = Post(body=form.post.data, author=current_user)
    #     db.session.add(post)
    #     db.session.commit()
    #     flash('Your post is now live!')
    #     return redirect(url_for('index'))
    # posts = Post.query.all()
    markets = Market.query.all()
    currencies = Currency.query.all()
    count_securities = 10
    count_companies = 10
    return render_template('index.html', title='Home', markets=markets, currencies=currencies,
                           count_companies=count_companies, count_securities=count_securities
                           )


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
    if not current_user.admin_tag:
        flash("Insufficient permission!")
        return redirect(url_for('index'))
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


# @app.route('/edit_profile', methods=['GET', 'POST'])
# @login_required
# def edit_profile():
#     form = EditProfileForm()
#     if form.validate_on_submit():
#         current_user.username = form.username.data
#         current_user.about_me = form.about_me.data
#         db.session.commit()
#         flash('Your changes have been saved.')
#         return redirect(url_for('edit_profile'))
#     elif request.method == 'GET':
#         form.username.data = current_user.username
#         form.about_me.data = current_user.about_me
#         return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# GET Methods #
@app.route('/markets/<market_id>/offer', methods=['GET'])  # login required???
def get_market_offer(market_id):
    data = Offer.query.filter_by(market_id=market_id).all()

    json_data = []

    for entry in data:
        json_data.append({
            'security_id': entry.security_id,
            # 'market_id': entry.market_id,
            'amount': entry.amount
        })

    return jsonify(json_data)


def time_to_string(time_obj):
    return time_obj.strftime('%H:%M:%S')


@app.route('/markets/<market_id>', methods=['GET'])
# @login_required
def market(market_id):
    market = Market.query.filter_by(market_id=market_id).first_or_404()
    transactions = Transactions.query \
        .filter_by(market_id=market_id) \
        .order_by(Transactions.transaction_id.desc()) \
        .limit(10) \
        .all()
    offer = Offer.query.filter_by(market_id=market_id).all()
    id = Market.query.filter_by(market_id=market_id).first().market_currency_id
    print(id)
    currency = Currency.query.filter_by(market_currency_id=id).first()

    json_data = []

    if request.headers.get('Accept') == 'application/json':
        json_data.append({
            'market_id': market.market_id,
            'market_name': market.market_name,
            'opens_at': time_to_string(market.opens_at),
            'closes_at': time_to_string(market.closes_at),
            'market_currency_id': market.market_currency_id,
            'market_fee': market.market_fee
        })

    # JSON Ausgabe
    if request.headers.get('Accept') == 'application/json':
        return jsonify(json_data)

    # HTML Render Ausgabe
    return render_template('market.html', market=market, transactions=transactions,
                           offer=offer, currency=currency)


@app.route('/markets', methods=['GET'])
# @login_required
def markets_all():
    markets = Market.query.all()
    json_data = {}

    for entry in markets:
        market_id = entry.market_id
        if market_id not in json_data:
            json_data[market_id] = []

        json_data[market_id].append({
            'market_id': entry.market_id,
            'market_name': entry.market_name,
            'opens_at': time_to_string(entry.opens_at),
            'closes_at': time_to_string(entry.closes_at),
            'market_currency_id': entry.market_currency_id,
            'market_fee': entry.market_fee
        })

    return jsonify(json_data)


@app.route('/markets/transactions', methods=['GET'])
# @login_required
def markets_transactions():  # eventuell id von einer börse mitgeben
    transactions = Transactions.query.all()
    json_data = []

    for entry in transactions:
        json_data.append([{
            'transaction_id': entry.transaction_id,
            'timestamp': time_to_string(entry.timestamp),
            'security_id': entry.security_id,
            'security_price': entry.security_price,
            'security_amount': entry.security_amount,
            'transaction_type': entry.transaction_type,
            'market_id': entry.market_id
        }])

    return jsonify(json_data)


# PUT Schnittstellen #

@app.route('/markets/<market_id>/buy', methods=['PUT'])
# @login_required
def buy(market_id):
    market = Market.query.filter_by(market_id=market_id).first_or_404(description="Börse nicht gefunden!")

    data = request.json
    security_id = data['security_id']
    amount = data['amount']
    url = 'http://127.0.0.1:50052/firmen/wertpapier/{}/kauf'.format(
        security_id)  # anpassen an Port der Firmenverwaltung
    get_url = 'http://127.0.0.1:50052/firmen/wertpapiere/{}'.format(security_id)

    get_security_info = requests.get(get_url)

    if get_security_info.status_code == 200:
        get_data = get_security_info.json()
        # print(get_data)
        for get_entry in get_data:
            security_price = get_entry['price']

    else:
        return "Fehler. Wertpapier nicht gefunden.", 400

    entry = Offer.query.filter_by(market_id=market_id, security_id=security_id).first_or_404(
        description="Wertpapier nicht vorhanden!")
    availableAmount = entry.amount

    if amount > availableAmount:
        message = "Es sind nur noch " + str(availableAmount) + " Stueck dieses Wertpapiers vorhanden! Erneut versuchen."

        return jsonify({'message': message}), 400

    else:
        entry.amount = availableAmount - amount
        data["market_fee"] = market.market_fee
        response = requests.put(url, data=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            newEntry = Transactions(security_id=security_id, security_price=security_price, security_amount=amount,
                                    transaction_type="Buy", market_id=market_id)
            db.session.add(newEntry)
            db.session.commit()
        else:
            db.session.rollback()
            return jsonify({'message': 'Fehler in der Anfrage!'}), 400

        return jsonify({'message': 'Kauf war erfolgreich!'}), 200


@app.route('/markets/<market_id>/sell', methods=['PUT'])
# @login_required
def sell(market_id):
    market = Market.query.filter_by(market_id=market_id).first_or_404(description="Börse nicht gefunden!")

    data = request.json
    security_id = data['security_id']
    amount = data['amount']

    entry = Offer.query.filter_by(market_id=market_id, security_id=security_id).first()
    url = 'http://127.0.0.1:50052/firmen/wertpapier/{}/verkauf'.format(
        security_id)  # anpassen an Port der Firmenverwaltung

    get_url = 'http://127.0.0.1:50052/firmen/wertpapiere/{}'.format(security_id)

    get_security_info = requests.get(get_url)

    if get_security_info.status_code == 200:
        get_data = get_security_info.json()
        # print(get_data)
        for get_entry in get_data:
            security_price = get_entry['price']

    else:
        return "Fehler. Wertpapier nicht gefunden.", 400

    if entry:
        entry.amount = entry.amount + amount
        data["market_fee"] = market.market_fee
        response = requests.put(url, data=data, headers={'Content-Type': 'application/json'})
        print(data)
        if response.status_code == 200:
            newEntry = Transactions(security_id=security_id, security_price=security_price, security_amount=amount,
                                    transaction_type="Sell", market_id=market_id)
            db.session.add(newEntry)
            db.session.commit()
            return jsonify(data), 200
        else:
            db.session.rollback()
            return jsonify({'message': 'Fehler in der Anfrage!'}), 400

    else:
        return jsonify({'message': 'Wertpapier wird an dieser Boerse nicht gehandelt!'}), 400


@app.route('/markets/<market_id>/offer', methods=['POST'])
def refresh_offer(market_id):
    global message
    market = Market.query.filter_by(market_id=market_id).first_or_404(description="Börse nicht gefunden!")
    data = request.get_json(force=True)
    print(data)
    if data is not None:
        if isinstance(data, list):
            # Daten sind eine Liste von Objekten
            for entry in data:
                security_id = entry['id']
                amount = entry['amount']

                if Offer.query.filter_by(security_id=security_id).first():
                    existing = Offer.query.filter_by(security_id=security_id, market_id=market_id).first()
                    existing.amount = amount
                else:
                    newEntry = Offer(market_id=market_id, security_id=security_id, amount=amount)
                    db.session.add(newEntry)

        elif isinstance(data, dict):
            # Daten sind ein einzelnes Objekt
            security_id = data['id']
            amount = data['amount']

            if Offer.query.filter_by(security_id=security_id, market_id=market_id).first():
                existing = Offer.query.filter_by(security_id=security_id, market_id=market_id).first()
                existing.amount = amount
                message = "Bestehendes Wertpapier aktualisiert!"
            else:
                newEntry = Offer(market_id=market_id, security_id=security_id, amount=amount)
                message = "Neues Angebot erfolgreich erstellt!"
                db.session.add(newEntry)

        db.session.commit()
        return message, 200
    else:
        return "Ungültige Anfrage", 400


# Firmenverwaltung simulation
@app.route('/wertpapier/<security_id>/verkauf', methods=['GET'])
# @login_required
def security_info(security_id):
    return jsonify({
        'security_id': 3,
        'name': "aktie1",
        'price': 100,
        'comp_id': 1,
        'amount': 99,
        'market_id': 1,
        'currency': "EUR"}), 200


@app.route('/markets/getcurrencies')
def get_currencies():
    url = "https://openexchangerates.org/api/currencies.json"
    response = requests.get(url)
    data = response.json()
    keys = data.keys()

    for entry in keys:
        name = data[str(entry)]
        newEntry = Currency(market_currency_name=name, market_currency_code=str(entry))
        db.session.add(newEntry)

    db.session.commit()
    return '', 200

#.label('id_market')
@app.route('/markets/create_csv')
def create_csv():
    data = db.session.query(Market.market_name, Market.market_id, Offer.amount,
                            Offer.security_id) \
        .join(Offer, Market.market_id == Offer.market_id, isouter=True)
    results = data.all()


    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    csv_writer.writerow([
        'Market Name',
        'Market ID',
        'Amount',
        'Security ID'
    ])

    for result in results:
        csv_writer.writerow([
            result.market_name,
            result.market_id,
            result.amount,
            result.security_id
        ])

    csv_text = csv_buffer.getvalue()

    return Response(
        csv_text,
        mimetype='text/csv',
        headers={'Content-disposition': 'attachment; filename=data.csv'}
    )


@app.route('/firmen/wertpapiere/<market_id>', methods=['GET'])
# @login_required
def securities_info(market_id):
    return jsonify({
        'security_id': 3,
        'name': "aktie1",
        'price': 100,
        'comp_id': 1,
        'amount': 99,
        'market_id': 1,
        'currency': "EUR"
    },
        {
            'security_id': 1,
            'name': "aktie1",
            'price': 100,
            'comp_id': 1,
            'amount': 1000,
            'market_id': 1,
            'currency': "EUR"
        }
    ), 200


@app.route('/firmen/wertpapier/<security_id>/kauf', methods=['PUT'])
# Info ausgabe wenn Wertpapier gekauft wurde
def sold_info(security_id):
    return '', 200


@app.route('/firmen/wertpapier/<security_id>/verkauf', methods=['PUT'])
# Info ausgabe wenn Wertpapier verkauft wurde
def bought_info(security_id):
    return '', 200
