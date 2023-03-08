from flask import Flask
from flask_socketio import SocketIO, emit
import logging
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import scoped_session, sessionmaker
from redis import Redis
import rq
import os
import sys
import openai
from dotenv import load_dotenv
from mygptapp.bing_search import BingSearchAPI
from mygptapp.rules import Rules
from mygptapp.openai_api import OpenAIAPI
#from mygptapp.actions import Actions

# get the grand-parent directory of the current file
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(script_dir, '.env')

# load the environment variables from the .env file
load_dotenv(dotenv_path=env_path)

# Add the parent directory to the system path
sys.path.append(os.path.dirname(script_dir))

# from Actions import {
# 	AddTodo,
# 	UpdateTodo,
# 	RemoveTodo,
# }

openai.api_key = os.getenv("OPENAI_API_KEY")
bing_search_api_key = os.getenv("BING_SEARCH_API_KEY")
bing_search_api = BingSearchAPI(bing_search_api_key)

rules = Rules()
#actions = Actions()
api = OpenAIAPI()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True # Reload templates on change
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
#app.config['PROPAGATE_EXCEPTIONS'] = True
#app.config['SECRET_KEY'] = 'secret!'
#toolbar = DebugToolbarExtension(app)
#app.jinja_env.auto_reload = True

logging_enabled = True
socketio = SocketIO(app, logger=logging_enabled, engineio_logger=logging_enabled)

# configure logging
handler = logging.StreamHandler()
formatter = logging.Formatter('\033[1;31m%(levelname)s\033[1;0m %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

db = SQLAlchemy(app)
ma = Marshmallow(app)

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# Set up application context
with app.app_context():
    Session = scoped_session(sessionmaker(bind=db.engine))

    redis=None
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        redis = Redis.from_url(redis_url)
    else:
        # handle the case when the REDIS_URL environment variable is not set
        print("error REDIS_URL not set")
        # exit
        exit()
    queue = rq.Queue(connection=redis)

from mygptapp.models import User, Conversation, Message, Todo

# create tables on app startup
@app.before_first_request
def create_tables():
    print("Creating tables...")
    try:
        db.create_all()
        # if there is no bot user in the database, create one
        if not User.query.filter_by(username="bot").first():
            bot = User(username="bot")
            db.session.add(bot)
            db.session.commit()
        # if there is no jakedowns user in the db, create one
        if not User.query.filter_by(username="jakedowns").first():
            jakedowns = User(username="jakedowns")
            db.session.add(jakedowns)
            db.session.commit()
        # if there is no conversation id 1 in the db, create one
        if not Conversation.query.filter_by(id=1).first():
            bot = User.query.filter_by(username="bot").first()
            jakedowns = User.query.filter_by(username="jakedowns").first()
            convo = Conversation(id=1,user_id=jakedowns.id,bot_id=bot.id)
            db.session.add(convo)
            db.session.commit()
        # if there is no conversation id 2 in the db, create one (bot's inner monologue)
        if not Conversation.query.filter_by(id=2).first():
            bot = User.query.filter_by(username="bot").first()
            convo = Conversation(id=2,user_id=bot.id,bot_id=bot.id)
            db.session.add(convo)
            db.session.commit()

    except Exception as e:
        print(e)
        print("Error creating tables")

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.teardown_request
def remove_session(exception=None):
    Session.remove()

from mygptapp.routes import *
