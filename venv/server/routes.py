import os
import random
import string
import json
import statistics
import logging

import numpy as np
from flask import redirect, render_template, url_for, request, session, flash
from flask_login import current_user, login_required, login_user, logout_user
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

from server import app, socketio

from .models import Users, Orders

from binance.client import Client
from binance.enums import *
client = Client('key1', 'key2')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')
    if login and password:
        user = Users.get_or_none(Users.login == login)
        if user is not None:
            if user and check_password_hash(user.password, password):
                login_user(user) 
                return redirect(url_for('dashboard'))
            else:
                flash('Login or password is not correct', 'danger')
        else:
            flash('User not found', 'danger')
    else:
        flash('Please fill login and password fields', 'warning')
    
    return render_template('signin.html.jinja')

@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not (login or password or password2):
            #flash('Please, fill all fields!')
            flash('fill fields', 'danger')
        elif password != password2:
            flash('Passwords are not equal!', 'warning')
        else:
            user = Users.get_or_none(Users.login == login)
            if user is not None:
                    flash('This login already exists!', 'danger')
                    return render_template('signup.html.jinja')
            else:
                hash_pwd = generate_password_hash(password)
                Users.create(login = login, password = hash_pwd, balance_usd=0, balance_btc=0, order_amount=0, ma=0)
                return redirect(url_for('login_page'))
    return render_template('signup.html.jinja')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        order_limit_amount = request.form.get('order_limit_amount')
        ma = request.form.get('ma')
        add = request.form.get('add')
        if current_user.is_authenticated:
            try:
                user = Users.get_or_none(Users.login == current_user.login)
                if order_limit_amount:
                    order_limit_update = Users.update(order_amount=float(order_limit_amount)).where(Users.login == current_user.login)
                    order_limit_update.execute()
                if ma:
                    ma_update = Users.update(ma=float(ma)).where(Users.login == current_user.login)
                    ma_update.execute()
                if add:
                    add_update = Users.update(balance_usd=float(current_user.balance_usd) + float(add)).where(Users.login == current_user.login)
                    add_update.execute()
                return redirect(url_for('dashboard'))
            except Exception as ex:
                logging.info(ex)
                return redirect(url_for('dashboard'))
    else:
        if current_user.is_authenticated:
            user = Users.get_or_none(Users.login == current_user.login)
            avg_price = client.get_avg_price(symbol='BTCUSDT')
            sum_balance = float(user.balance_btc) * float(avg_price['price']) + float(user.balance_usd)
            order_list = list()
            try:
                orders = Orders.select().where(Orders.user_id == current_user.id).order_by(Orders.id.desc())
                order_list = list([order for order in orders])
                logging.info(order_list)
            except Exception as ex:
                logging.info(ex)
            return render_template('index.html.jinja', current=user, sum_balance=sum_balance, order_list=order_list)
        else:
            return redirect(url_for('login_page'))
