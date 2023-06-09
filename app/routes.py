import csv
import io
import json
from datetime import datetime, time

import pandas as pd
import requests
from flask import render_template, flash, redirect, url_for, request, jsonify, Response
from flask_login import current_user, login_user, logout_user
from flask_login import login_required
from sqlalchemy import func
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateNewMarketForm, EditMarketForm
from app.models import User, Market, Transactions, Offer, Currency


@app.context_processor
def inject_datetime():
    return {'current_time': datetime.utcnow()}


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required  # nur sichtbar für eingeloggte User
def index():
    markets = Market.query.all()
    currencies = Currency.query.all()

    return render_template('index.html', title='Home', markets=markets, currencies=currencies,
                           count_companies=count_companies, count_securities=count_securities,
                           get_securities=get_securities)


def count_securities(market_id):
    number = Offer.query.filter_by(market_id=market_id).count()
    return number


def count_companies(market_id):
    offers = Offer.query.filter_by(market_id=market_id).all()

    if get_securities():
        security_info_json = get_securities()
    else:
        return None

    company_list = []

    for entry in offers:
        for security in security_info_json:
            if entry.security_id == security['id']:
                company_list.append(security['comp_id'])

    unique_list = list(dict.fromkeys(company_list))

    return len(unique_list)


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
        user = User(username=form.username.data)
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


@app.route('/deletemarket/<market_id>', methods=['GET'])
def delete_market(market_id):
    if not current_user.admin_tag:
        flash("Insufficient permission!")
        return redirect(url_for('index'))
    market = Market.query.get(market_id)
    securities = Offer.query.filter_by(market_id=market_id).all()

    if len(securities) > 0:
        flash('There are still securities available on the selected market! Cannot delete market.')
        return redirect(request.referrer or url_for('index'))

    db.session.delete(market)
    db.session.commit()

    flash('Market: "' + market.market_name + '" gelöscht!')
    return redirect(request.referrer or url_for('index'))


@app.route('/editmarket/<market_id>', methods=['GET', 'POST'])
def edit_market(market_id):
    if not current_user.admin_tag:
        flash("Insufficient permission!")
        return redirect(url_for('index'))

    market = Market.query.get(market_id)

    form = EditMarketForm(obj=market)

    if form.validate_on_submit():
        market.market_name = form.market_name.data
        market.market_currency_id = form.market_currency_id.data
        market.market_country = form.market_country.data
        market.market_fee = form.market_fee.data
        market.opens_at = form.opens_at.data
        market.closes_at = form.closes_at.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))

    elif request.method == 'GET':
        return render_template('edit_market.html', title='Edit Market', form=form)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# ============================================================================================
# ********************************************************************************************
# GET Methods #
# ********************************************************************************************
# ============================================================================================
@app.route('/markets/<market_id>/offer', methods=['GET'])
def get_market_offer(market_id):
    data = Offer.query.filter_by(market_id=market_id).all()

    json_data = []

    for entry in data:
        json_data.append({
            'security_id': entry.security_id,
            'amount': entry.amount
        })

    return jsonify(json_data)


def time_to_string(time_obj):
    return time_obj.strftime('%Y-%m-%d %H:%M:%S')





@app.route('/markets/<market_id>', methods=['GET'])
def market(market_id):
    market = Market.query \
        .filter_by(market_id=market_id) \
        .first_or_404()

    currency = Currency.query\
        .filter_by(market_currency_id=market.market_currency_id)\
        .first_or_404()

    if request.headers.get('Accept') == 'application/json':
        json_data = {
            'market_id': market_id,
            'market_name': market.market_name,
            'opens_at': time_to_string(market.opens_at),
            'closes_at': time_to_string(market.closes_at),
            'market_currency_id': market.market_currency_id,
            'market_fee': market.market_fee,
            'market_currency_code': currency.market_currency_code
        }
        return jsonify(json_data)

    security_info_json = None

    if get_securities():
        security_info_json = get_securities()

        transactions = Transactions.query.filter_by(market_id=market_id).all()
        company_counts = {}

        for transaction in transactions:
            security_id = transaction.security_id
            for security in security_info_json:
                if security['id'] == security_id:
                    comp_id = security.get('comp_id')
                    if comp_id in company_counts:
                        company_counts[comp_id]['count'] += transaction.security_amount
                    else:
                        company_counts[comp_id] = {'count': transaction.security_amount}
        print(security_info_json)
        # Sortiere die Unternehmen nach der Anzahl der gehandelten Wertpapiere in absteigender Reihenfolge
        top_companies = []
        for comp_id in sorted(company_counts, key=lambda x: company_counts[x]['count'], reverse=True):
            top_companies.append((comp_id, company_counts[comp_id]))


        # nur die besten 3 wählen
        top_3_companies = top_companies[:3]
        top_3_companies_with_names = []

        for comp_id, company_info in top_3_companies:
            company_data = {'count': company_info['count'], 'name': get_comp_name(comp_id)}

            top_3_companies_with_names.append((comp_id, company_data))

        while len(top_3_companies_with_names) < 3:
            company_data = {'count': "-", 'name': "-"}
            top_3_companies_with_names.append((None, company_data))
    else:
        top_3_companies_with_names = None

    market = Market.query \
        .filter_by(market_id=market_id) \
        .first_or_404()

    transactions = Transactions.query \
        .filter_by(market_id=market_id) \
        .order_by(Transactions.transaction_id.desc()) \
        .limit(100) \
        .all()

    offers = Offer.query \
        .filter_by(market_id=market_id) \
        .with_entities(Offer.security_id, func.sum(Offer.amount).label('available_amount')) \
        .group_by(Offer.security_id) \
        .order_by(Offer.security_id.asc()) \
        .all()

    id = Market.query \
        .filter_by(market_id=market_id) \
        .first() \
        .market_currency_id

    currency = Currency \
        .query \
        .filter_by(market_currency_id=id) \
        .first()

    # HTML Render Ausgabe
    return render_template('market.html', title=market.market_name, market=market, transactions=transactions,
                           offer=offers, currency=currency, security_info=security_info_json,
                           top_companies=top_3_companies_with_names, get_name=get_name, get_price=get_price,
                           get_comp_name=get_comp_name, get_comp_name_from_sec=get_comp_name_from_sec)


@app.route('/markets', methods=['GET'])
# @login_required
def markets_all():
    markets = Market.query.all()
    json_data = {}

    for entry in markets:
        market_id = entry.market_id
        if market_id not in json_data:
            json_data[market_id] = []

        currency = Currency.query\
            .filter_by(market_currency_id=entry.market_currency_id)\
            .first_or_404()

        json_data[market_id].append({
            'market_id': entry.market_id,
            'market_name': entry.market_name,
            'opens_at': time_to_string(entry.opens_at),
            'closes_at': time_to_string(entry.closes_at),
            'market_currency_id': entry.market_currency_id,
            'market_currency_code': currency.market_currency_code,
            'market_fee': entry.market_fee
        })

    return jsonify(json_data)


@app.route('/markets/transactions', methods=['GET'])
# @login_required
def markets_transactions():  # eventuell id von einer börse mitgeben
    transactions = Transactions.query.all()
    json_data = []

    for entry in transactions:
        json_data.append({
            'transaction_id': entry.transaction_id,
            'timestamp': time_to_string(entry.timestamp),
            'security_id': entry.security_id,
            'security_price': entry.security_price,
            'security_amount': entry.security_amount,
            'transaction_type': entry.transaction_type,
            'market_id': entry.market_id
        })

    return jsonify(json_data)

@app.route('/markets/currency', methods=['GET'])
# @login_required
def markets_currencies():  # eventuell id von einer börse mitgeben
    currencies = Currency.query.all()
    json_data = []

    for entry in currencies:
        json_data.append({
            'market_currency_id': entry.market_currency_id,
            'market_currency_name': entry.market_currency_name,
            'market_currency_code': entry.market_currency_code,
        })

    return jsonify(json_data)
# ============================================================================================
# ********************************************************************************************
# PUT Methods #
# ********************************************************************************************
# ============================================================================================
@app.route('/markets/<market_id>/buy', methods=['PUT'])
def buy(market_id):
    market = Market.query.filter_by(market_id=market_id).first_or_404(description="Börse nicht gefunden!")

    fees = market.market_fee

    currency_id = market.market_currency_id
    currency = Currency.query \
        .filter_by(market_currency_id=currency_id) \
        .first_or_404(description="Waehrung nicht verfügbar") \
        .market_currency_code

    data = request.json
    security_id = data['security_id']
    amount = data['amount']

    security_price = get_price(security_id)
    if security_price == "Not found":
        return "Fehler. Wertpapier nicht gefunden.", 400

    if security_price == "Not found - Check FW.":
        return "Verbindungsfehler. Check FW.", 400

    offers = Offer \
        .query \
        .filter_by(market_id=market_id, security_id=security_id) \
        .order_by(Offer.offer_id.desc()) \
        .all()

    total_amount = Offer.query \
        .filter_by(market_id=market_id, security_id=security_id) \
        .with_entities(func.sum(Offer.amount).label('available_amount')) \
        .first()

    if total_amount:
        available_amount = total_amount.available_amount or 0
    else:
        available_amount = 0

    # wenn insgesamt weniger von diesem security vorhanden ist
    if amount > available_amount:
        if available_amount == 0:
            message = "Dieses Wertpapier ist leider nicht mehr an dieser Börse verfügbar. Vorgang abgebrochen."
            return jsonify({'message': message}), 400

        message = "Es sind nur noch " + str(available_amount) + \
                  " Stueck dieses Wertpapiers vorhanden! Erneut versuchen."
        return jsonify({'message': message}), 400

    i = 0
    sold_amount = 0

    while amount > 0 and i < len(offers):
        offer = Offer.query.get(offers[i].offer_id)
        if offers[i].company_id is None:
            id = offers[i].depot_id
            typ = "Person"
            # TODO anpassen an DEPOT ID
            url = "http://127.0.0.1:50050/depot/wertpapier/verkauf/" + str(id)

        else:
            id = offers[i].security_id
            typ = "Company"
            url = "http://127.0.0.1:50051/firmen/wertpapier/verkauf/" + str(id)

        if amount >= offers[i].amount:
            sold_amount = offers[i].amount
            amount = amount - offers[i].amount

            db.session.delete(offer)

        else:
            sold_amount = amount
            offers[i].amount = offers[i].amount - amount
            amount = 0

            # info an den besitzer vom jeweiligen angebot in der liste
        data = {'id': offer.offer_id, 'typ': typ, 'amount': sold_amount, 'seller_id': id, 'fees': fees,
                'price': security_price * sold_amount, 'currency': currency}

        try:
            response = requests.put(url, json=data)
        except requests.exceptions.ConnectionError as e:
            return jsonify({'message': 'Es gab ein Problem mit der Verbindung. Kaufvorgang abgebrochen.'}), 404

        if response.status_code != 200:
            return jsonify({'message': 'Es gab ein Problem mit der Anfrage. Kaufvorgang abgebrochen.'}), 404

        print("Nachricht an Seller: " + str(data) + ", Nachricht von Seller: " + str(response))

        i = i + 1

        newEntry = Transactions(security_id=security_id, security_price=security_price, security_amount=sold_amount,
                            transaction_type="Buy", market_id=market_id)
    db.session.add(newEntry)
    db.session.commit()

    return jsonify({'message': 'Kauf war erfolgreich!'}), 200


# ============================================================================================
# ********************************************************************************************
# POST Methods #
# ********************************************************************************************
# ============================================================================================
@app.route('/deleteoffer/<security_id>', methods=['POST'])
def delete_offer(security_id):

    offer = Offer.query.get(security_id)


    db.session.delete(offer)
    db.session.commit()

    flash('Offer: "' + offer.offer_id + '" gelöscht!')
    return "Offer gelöscht!", 200

def create_offer_and_transaction(market_id, security_id, amount, company_id, depot_id, security_price):
    new_entry = Offer(market_id=market_id, security_id=security_id, amount=amount,
                      company_id=company_id, depot_id=depot_id)
    new_transaction = Transactions(security_id=security_id, security_price=security_price,
                                   security_amount=amount, transaction_type="Sell", market_id=market_id)
    db.session.add(new_entry)
    db.session.add(new_transaction)


@app.route('/markets/<market_id>/offer', methods=['POST'])
def refresh_offer(market_id):
    global message
    market = Market.query.filter_by(market_id=market_id).first_or_404(description="Börse nicht gefunden!")

    id = Market.query \
        .filter_by(market_id=market_id) \
        .first() \
        .market_currency_id

    currency_obj = Currency \
        .query \
        .filter_by(market_currency_id=id) \
        .first()

    data = request.get_json()

    if data is not None:
        if isinstance(data, list):
            # Daten sind eine Liste von Objekten
            for entry in data:
                security_id = entry.get('id')
                amount = entry.get('amount')
                company_id = entry.get('comp_id')  # TODO achtung auf Bezeichnung der Werte
                depot_id = entry.get('depot_id')
                security_price = entry.get('price')
                currency = entry.get('currency')
                if currency != currency_obj.market_currency_code:
                    return "Währung der Boerse ist: " + str(currency.market_currency_code), 406
                create_offer_and_transaction(market_id, security_id, amount, company_id, depot_id, security_price)

            message = str(len(data)) + ' neue Angebote wurden erfolgreich erstellt!'

        elif isinstance(data, dict):
            # Daten sind ein einzelnes Objekt
            security_id = data.get('id')
            amount = data.get('amount')
            company_id = data.get('comp_id')
            depot_id = data.get('depot_id')
            security_price = data.get('price')
            currency = data.get('currency')
            if currency != currency_obj.market_currency_code:
                return "Währung der Boerse ist: " + str(currency_obj.market_currency_code), 400

            create_offer_and_transaction(market_id, security_id, amount, company_id, depot_id, security_price)

            message = "Neues Angebot erfolgreich erstellt!"

        db.session.commit()
        return message, 200

    else:
        return "Ungültige Anfrage", 400


# ============================================================================================
# ********************************************************************************************
# USP - CSV Creation #
# ********************************************************************************************
# ============================================================================================

@app.route('/markets/create_csv', methods=['GET'])
def create_csv():

    security_info_json = get_securities()

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
        'Security ID',
        'Security Name'
    ])

    for result in results:
        security_name = None
        if security_info_json:
            for security in security_info_json:
                if result.security_id == security['id']:
                    security_name = security['name']

        csv_writer.writerow([
            result.market_name,
            result.market_id,
            result.amount,
            result.security_id,
            security_name
        ])

        csv_text = csv_buffer.getvalue()

    return Response(
        csv_text,
        mimetype='text/csv',
        headers={'Content-disposition': 'attachment; filename=market_overview.csv'}
    )


@app.route('/markets/excel_creation', methods=['GET', 'POST'])
def excel_creation():
    if not current_user.admin_tag:
        flash("Insufficient permission!")
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['excel-file']
        if file:
            markets = []
            # dataframe - aus pandas, für excel import und zur weiteren verwendung
            df = pd.read_excel(file)

            for index, row in df.iterrows():
                market_name = row['name']
                currency = row['currency_id']
                country = row['country']
                fee = row['fee']
                opens_at_str = row['opens_at']
                closes_at_str = row['closes_at']

                market_data = {
                    'market_name': market_name,
                    'opens_at': opens_at_str,
                    'closes_at': closes_at_str,
                    'market_currency_id': currency,
                    'market_country': country,
                    'market_fee': fee
                }

                markets.append(market_data)

            markets_json = json.dumps(markets, default=serialize_time)

            if not markets_json:
                flash('No Excel File given!')
                return redirect(url_for('excel_creation'))

            markets_list = json.loads(markets_json)

            if request.method == 'POST':
                for market_data in markets_list:
                    opens_at = time.fromisoformat(market_data['opens_at'])
                    closes_at = time.fromisoformat(market_data['closes_at'])

                    market_data['opens_at'] = opens_at
                    market_data['closes_at'] = closes_at
                    market_data.pop('id', None)
                    # Transformiere das Wörterbuch zurück in ein Market-Objekt
                    market = Market(**market_data)

                    db.session.add(market)
                db.session.commit()

                flash('Successfully created markets!')
                return redirect(url_for('index'))

    return render_template("market_creation_xlsx.html")


# ============================================================================================
# ********************************************************************************************
# Allgemeine Methoden
# ********************************************************************************************
# ============================================================================================
def get_name(security_id):
    get_url = 'http://127.0.0.1:50051/firmen/wertpapiere/{}'.format(security_id)

    try:
        get_security_info = requests.get(get_url)
    except requests.exceptions.ConnectionError as e:
        return -2

    if get_security_info.status_code == 200:
        get_data = get_security_info.json()
        security_name = get_data['name']
        return security_name

    else:
        return "Not found."


def get_price(security_id):
    get_url = 'http://127.0.0.1:50051/firmen/wertpapiere/{}'.format(security_id)

    try:
        get_security_info = requests.get(get_url)
    except requests.exceptions.ConnectionError as e:
        return "Not found - Check FW."

    if get_security_info.status_code == 200:
        get_data = get_security_info.json()
        security_price = get_data['price']
        return round(security_price, 2)

    else:
        return "Not found"


def get_securities():
    url = "http://127.0.0.1:50051/firmen/wertpapiere"
    try:
        security_info = requests.get(url)
        security_info_json = security_info.json()
    except requests.exceptions.ConnectionError as e:
        return None
    print(security_info_json)
    return security_info_json


def get_comp_name_from_sec(security_id):
    get_companies_url = "http://127.0.0.1:50051/firmen"

    try:
        companies_info = requests.get(get_companies_url)
        companies_info_json = companies_info.json()
    except requests.exceptions.ConnectionError as e:
        companies_info_json = []

    securities = get_securities()

    comp_id = -1
    if securities:
        for security in securities:
            if security['id'] == security_id:
                comp_id = security.get('comp_id')

        for company in companies_info_json:
            if comp_id == company.get('id'):
                return company.get('company_name')

    return "Not Found"

def get_comp_name(comp_id):
    get_companies_url = "http://127.0.0.1:50051/firmen"
    try:
        companies_info = requests.get(get_companies_url)
        companies_info_json = companies_info.json()
    except requests.exceptions.ConnectionError as e:
        companies_info_json = []

    print(companies_info_json)

    for company in companies_info_json:
        if comp_id == company.get('id'):
            return company.get('company_name')

    return "Not Found"

def serialize_time(obj):
    if isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# ============================================================================================
# ********************************************************************************************
# Zur einmaligen Befüllung der Currencies:
# ********************************************************************************************
# ============================================================================================

@app.route('/markets/getcurrencies')
# nur für einmalige initialisierung der Currency Tabelle (potentiel auch automatische aktualisierung)
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


# TODO Nur 5 währungen EUR, USD, CHF, SEK, JPY

# ============================================================================================
# ********************************************************************************************
# FIRMENVERWALTUNG DUMMY Methods #
# ********************************************************************************************
# ============================================================================================
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


@app.route('/firmen/wertpapiere', methods=['GET'])
# @login_required
def securities_info():
    return jsonify({
        'id': 3,
        'name': "KEBA A(3)",
        'price': 100,
        'comp_id': 1,
        'amount': 99,
        'market_id': 1,
        'currency': "EUR"
    },
        {
            'id': 1,
            'name': "Voestalpine A(1)",
            'price': 100,
            'comp_id': 1,
            'amount': 1000,
            'market_id': 1,
            'currency': "EUR"
        },
        {
            'id': 6,
            'name': "aktie 6",
            'price': 16,
            'comp_id': 3,
            'amount': 600,
            'market_id': 3,
            'currency': "USD"
        },
        {
            'id': 67,
            'name': "aktie 67",
            'price': 16,
            'comp_id': 3,
            'amount': 600,
            'market_id': 3,
            'currency': "USD"
        },
        {
            'id': 2,
            'name': "aktie 2",
            'price': 16,
            'comp_id': 3,
            'amount': 600,
            'market_id': 3,
            'currency': "USD"
        },
        {
            'id': 32,
            'name': "aktie 32",
            'price': 16,
            'comp_id': 8,
            'amount': 600,
            'market_id': 3,
            'currency': "USD"
        }
    ), 200


@app.route('/firmen/wertpapiere/<security_id>', methods=['GET'])
def get_security_info(security_id):
    return {
        "amount": 21932,
        "comp_id": 5,
        "currency": "EUR",
        "id": 1,
        "market_id": 3,
        "name": "Voestalpine A",
        "price": 74.19
    }, 200


@app.route('/firmen/wertpapier/kauf/<security_id>', methods=['PUT'])
# Info ausgabe wenn Wertpapier gekauft wurde
def sold_info(security_id):
    data = request.get_json()
    return data, 200


@app.route('/firmen/wertpapier/verkauf/<security_id>', methods=['PUT'])
# Info ausgabe wenn Wertpapier verkauft wurde
def bought_info(security_id):
    data = request.get_json()
    return data, 200
