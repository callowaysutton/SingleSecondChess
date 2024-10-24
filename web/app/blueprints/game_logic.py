from flask import Blueprint, request, flash, render_template, redirect, g
from app import app, db, client
from app.models import User, Bot, Game, Leaderboard
import magic, itertools, subprocess, uuid

game_logic = Blueprint("game_logic", __name__)

# We will handle the game logic in this file. We will create a new game, play a game, and update the leaderboard based on the results of the game.

# Make a job queue to handle games, so that we can play multiple games at once. It should be all permutations of the bots in the database. We will use the itertools library to generate all permutations of the bots in the database. We will then create a new game for each permutation and add it to the job queue.

# Get all the bots from the database
def get_bots():
    return Bot.query.all()

from flask import render_template, request
from flask_socketio import SocketIO, emit
import subprocess
import uuid
import os

socketio = SocketIO(app)

# Assume necessary imports and database setup here
# from models import Bot, Leaderboard, Game, db

# Define the 'play_game' event handler
@socketio.on('play_game')
def handle_play_game(data):
    p1_bot_id = data['p1_bot_id']
    p2_bot_id = data['p2_bot_id']
    socket_id = request.sid
    # Start the game in a background thread
    socketio.start_background_task(target=create_game, p1_bot_id=p1_bot_id, p2_bot_id=p2_bot_id, socket_id=socket_id)

def create_game(p1_bot_id, p2_bot_id, socket_id):
    # Retrieve bots from database
    with app.app_context():
        p1_bot = Bot.query.filter_by(id=p1_bot_id).first()
        p2_bot = Bot.query.filter_by(id=p2_bot_id).first()

    # Create unique bin directory
    bin_dir = f"/tmp/{uuid.uuid4()}"

    os.makedirs(bin_dir, exist_ok=True)

    # Write binaries to files
    with open(f"{bin_dir}/p1", "wb") as f:
        f.write(p1_bot.binary)

    with open(f"{bin_dir}/p2", "wb") as f:
        f.write(p2_bot.binary)

    # Make binaries executable
    os.chmod(f"{bin_dir}/p1", 0o755)
    os.chmod(f"{bin_dir}/p2", 0o755)

    # Create the command
    command = [
        "docker",
        "run",
        "--cap-add",
        "PERFMON",
        "--security-opt=no-new-privileges",
        "--read-only",
        "--network=none",
        "--memory-swap=0",
        "--memory=0",
        "--cpus=1",
        "-v",
        f"{bin_dir}/p1:/bin/p1",
        "-v",
        f"{bin_dir}/p2:/bin/p2",
        "callowaysutton/ssc-runner",
    ]

    # Run the command and read output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    output_lines = []
    for line in iter(process.stdout.readline, ''):
        if not line:
            break
        output_lines.append(line)
        socketio.emit('game_output', {'data': line}, room=socket_id)

    process.stdout.close()
    process.wait()

    # Process the output as before
    result = ''.join(output_lines)

    # Delete the directory
    subprocess.run(["rm", "-rf", bin_dir])

    # Process game result and update database
    lines = result.strip().split("\n")
    winner_line = lines[-1]
    reason_line = lines[-2] if len(lines) >= 2 else ""

    with app.app_context():
        # Logic to determine the winner and update the leaderboard
        if winner_line == "Player 1 wins!":
            winner = p1_bot_id
            # Update leaderboard for Player 1
            leaderboard = Leaderboard.query.filter_by(bot_id=p1_bot_id).first()
            leaderboard.wins += 1
            leaderboard.games_played += 1
            db.session.commit()
            # Update leaderboard for Player 2
            leaderboard = Leaderboard.query.filter_by(bot_id=p2_bot_id).first()
            leaderboard.losses += 1
            leaderboard.games_played += 1
            db.session.commit()
        elif winner_line == "Player 2 wins!":
            winner = p2_bot_id
            # Update leaderboard for Player 2
            leaderboard = Leaderboard.query.filter_by(bot_id=p2_bot_id).first()
            leaderboard.wins += 1
            leaderboard.games_played += 1
            db.session.commit()
            # Update leaderboard for Player 1
            leaderboard = Leaderboard.query.filter_by(bot_id=p1_bot_id).first()
            leaderboard.losses += 1
            leaderboard.games_played += 1
            db.session.commit()
        elif winner_line == "Draw!":
            winner = None
            # Update leaderboard for both players
            leaderboard_p1 = Leaderboard.query.filter_by(bot_id=p1_bot_id).first()
            leaderboard_p1.draws += 1
            leaderboard_p1.games_played += 1
            leaderboard_p2 = Leaderboard.query.filter_by(bot_id=p2_bot_id).first()
            leaderboard_p2.draws += 1
            leaderboard_p2.games_played += 1
            db.session.commit()

        # Create new game object and add to database
        new_game = Game(
            player1_id=p1_bot_id,
            player2_id=p2_bot_id,
            winner_id=winner,
            is_draw=winner is None,
            moves=result,
        )
        db.session.add(new_game)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Handle exception

    # Emit game result to client
    socketio.emit('game_result', {'winner': winner_line, 'reason': reason_line}, room=socket_id)

# Route to serve the game page
@game_logic.route('/play/<uuid:p1_bot_id>/<uuid:p2_bot_id>')
async def play_game(p1_bot_id, p2_bot_id):
    return render_template('play_game.html', p1_bot_id=p1_bot_id, p2_bot_id=p2_bot_id)

@game_logic.route("/bots/duel")
async def duel():
    if not client.isAuthenticated():
        flash("You must be signed in to play a game.")
        return redirect("/sign-in")
    return render_template("duel.html", bots = get_bots(), user=client.isAuthenticated())