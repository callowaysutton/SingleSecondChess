if __name__ == "__main__":
    from app import app, db
    from app.models import User, Bot, Game, Leaderboard

    with app.app_context():
        db.drop_all()
        db.create_all()