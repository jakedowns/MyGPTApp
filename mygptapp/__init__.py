from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import scoped_session, sessionmaker
from redis import Redis
import rq
import os
import sys
import openai
from dotenv import load_dotenv

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

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True # Reload templates on change
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.jinja_env.auto_reload = True

db = SQLAlchemy(app)
ma = Marshmallow(app)

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

from mygptapp.models import User, Message, Conversation, Todo

@app.before_first_request
def create_tables():
    print("Creating tables...")
    db.create_all()
    # if there is no bot user in the database, create one
    if not User.query.filter_by(username="bot").first():
        bot = User(username="bot")
        db.session.add(bot)
        db.session.commit()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.teardown_request
def remove_session(exception=None):
    Session.remove()

from mygptapp.routes import *
