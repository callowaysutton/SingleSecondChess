from app.blueprints.web_logic import web_logic
from app.blueprints.game_logic import game_logic
from app import app

app.register_blueprint(web_logic)
app.register_blueprint(game_logic)