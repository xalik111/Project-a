from flask import Flask, jsonify, render_template_string, request
from flask_login import LoginManager
from flask_socketio import SocketIO
import threading
import atexit
import logging
import datetime

logging.basicConfig(filename='test.log', level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'somesecretsalt'

manager = LoginManager(app)
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

from server import models, routes
from server.autothread import start_thread
start_thread()