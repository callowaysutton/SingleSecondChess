from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    uuid = db.Column(db.String, primary_key=True, default=generate_uuid)
    email = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String, nullable=False, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bots = db.relationship("Bot", backref="owner", lazy=True)


class Bot(db.Model):
    __tablename__ = "bots"

    uuid = db.Column(db.String, primary_key=True, default=generate_uuid)
    name = db.Column(db.String, nullable=False)
    binary = db.Column(db.LargeBinary, nullable=False)
    owner_id = db.Column(db.String, db.ForeignKey("users.uuid"), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    games = db.relationship("Game", backref="bot", lazy=True)
    rankings = db.relationship("Leaderboard", backref="bot", lazy=True)


class Game(db.Model):
    __tablename__ = "games"

    uuid = db.Column(db.String, primary_key=True, default=generate_uuid)
    p1_bot_id = db.Column(db.String, db.ForeignKey("bots.uuid"), nullable=False)
    p2_bot_id = db.Column(db.String, db.ForeignKey("bots.uuid"), nullable=False)
    winner = db.Column(
        db.String, nullable=True
    )  # UUID of the winning bot or None for a draw
    game_logs = db.Column(db.Text, nullable=True)


class Leaderboard(db.Model):
    __tablename__ = "leaderboards"

    bot_id = db.Column(db.String, db.ForeignKey("bots.uuid"), primary_key=True)
    ranking = db.Column(db.Integer, nullable=False)
    game_wins = db.Column(db.Integer, default=0)
    game_losses = db.Column(db.Integer, default=0)
    game_draws = db.Column(db.Integer, default=0)
