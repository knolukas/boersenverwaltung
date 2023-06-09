from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from sqlalchemy import Column, Integer, DateTime, Boolean, String, Float, Text, ForeignKey, Time


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))
    last_seen = Column(DateTime, default=datetime.utcnow)
    admin_tag = Column(Boolean, default=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.username.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?s={}'.format(
            digest, size)


class Post(db.Model):
    id = Column(Integer, primary_key=True)
    body = Column(String(140))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Market(db.Model):
    market_id = Column(Integer, primary_key=True)
    market_name = Column(Text, unique=True, nullable=False)
    opens_at = Column(Time, nullable=False)
    closes_at = Column(Time, nullable=False)
    market_currency_id = Column(Integer, nullable=False)
    market_country = Column(Text, nullable=False)
    market_fee = Column(Float, nullable=False)

    def __repr__(self):
        return '<Market {}>'.format(self.market_name)


class Transactions(db.Model):
    transaction_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    security_id = Column(Integer, nullable=False)
    security_price = Column(Float, nullable=False)
    security_amount = Column(Integer, nullable=False)
    transaction_type = Column(Text, nullable=False)
    market_id = Column(Integer, ForeignKey('market.market_id'))

    def __repr__(self):
        return '<Transaction {}>'.format(self.transaction_id)


class Currency(db.Model):
    market_currency_id = Column(Integer, primary_key=True)
    market_currency_name = Column(Text, nullable=False)
    market_currency_code = Column(Text, nullable=False)


    def __repr__(self):
        return '<Currency {}>'.format(self.market_currency_id)


class Offer(db.Model):
    security_id = Column(Integer, nullable=False)
    market_id = Column(Integer, ForeignKey('market.market_id', name='fk_offer_market_id'), nullable=False)
    amount = Column(Integer, nullable=False)
    offer_id = Column(Integer, nullable=False, primary_key=True)

    def __repr__(self):
        return '<Offer {}>'.format(self.security_id, self.market_id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
