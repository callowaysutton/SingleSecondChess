import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import random

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

app = Flask(__name__)

# Get the DATABASE_URI from environment variables
database_uri = os.getenv("DATABASE_URI")
print(f"DATABASE_URI: {database_uri}")

# Check if the URI is None or empty
if not database_uri:
    logging.error("DATABASE_URI is not set or is empty.")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CORS_HEADERS"] = "Content-Type"
    app.config["SECRET_KEY"] = random.randbytes(32)

    try:
        db.init_app(app)
        migrate.init_app(app, db)
        cors.init_app(app)
    except Exception as e:
        logging.error(f"Error initializing app: {e}")

from logto import LogtoClient, LogtoConfig, Storage, UserInfoScope
from flask import session
from typing import Union


class SessionStorage(Storage):
    def get(self, key: str) -> Union[str, None]:
        return session.get(key, None)

    def set(self, key: str, value: Union[str, None]) -> None:
        session[key] = value

    def delete(self, key: str) -> None:
        session.pop(key, None)


client = LogtoClient(
    LogtoConfig(
        endpoint=os.getenv("LOGTO_ENDPOINT"),
        appId=os.getenv("LOGTO_APP_ID"),
        appSecret=os.getenv("LOGTO_APP_SECRET"),
        scopes=[
            UserInfoScope.email,
            UserInfoScope.organizations,
            UserInfoScope.organization_roles,
            UserInfoScope.custom_data,
            UserInfoScope.profile,
        ],  # Update scopes as needed
    ),
    storage=SessionStorage(),
)

if app.debug:
    with app.app_context():
        from app.models import User, Bot, Game, Leaderboard

        db.drop_all()
        db.create_all()

from app import routes
