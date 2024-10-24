import uuid, datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=False, nullable=False, default='Anonymous')
    email = Column(String, unique=True, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    bots = relationship('Bot', back_populates='owner', cascade='all, delete-orphan')


class Bot(db.Model):
    __tablename__ = 'bots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    binary = Column(db.LargeBinary, nullable=False)
    icon = Column(db.LargeBinary, nullable=True)

    owner = relationship('User', back_populates='bots')
    games_as_player1 = relationship(
        'Game',
        back_populates='player1',
        foreign_keys='Game.player1_id',
        cascade='all, delete-orphan'
    )
    games_as_player2 = relationship(
        'Game',
        back_populates='player2',
        foreign_keys='Game.player2_id',
        cascade='all, delete-orphan'
    )
    leaderboard_entry = relationship(
        'Leaderboard',
        uselist=False,
        back_populates='bot',
        cascade='all, delete-orphan'
    )


class Game(db.Model):
    __tablename__ = 'games'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    player1_id = Column(UUID(as_uuid=True), ForeignKey('bots.id'), nullable=False)
    player2_id = Column(UUID(as_uuid=True), ForeignKey('bots.id'), nullable=False)
    winner_id = Column(UUID(as_uuid=True), ForeignKey('bots.id'), nullable=True)
    is_draw = Column(Boolean, default=False, nullable=False)
    moves = Column(db.Text, nullable=False)  # Stores moves as a JSON array
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    # Additional game fields can be added here

    player1 = relationship(
        'Bot',
        foreign_keys=[player1_id],
        back_populates='games_as_player1'
    )
    player2 = relationship(
        'Bot',
        foreign_keys=[player2_id],
        back_populates='games_as_player2'
    )
    winner = relationship('Bot', foreign_keys=[winner_id])


class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'

    bot_id = Column(UUID(as_uuid=True), ForeignKey('bots.id'), primary_key=True)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    draws = Column(Integer, default=0, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)

    bot = relationship('Bot', back_populates='leaderboard_entry')
