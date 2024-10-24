from flask import Blueprint, request, flash, render_template, redirect, g
from app import app, db, client
from app.models import User, Bot, Game, Leaderboard

import magic

web_logic = Blueprint("web_logic", __name__)


@web_logic.route("/")
async def index():
    return render_template("homepage.html", user=client.isAuthenticated())

@web_logic.route("/bots")
async def bots():
    if not client.isAuthenticated():
        return redirect("/sign-in")
    # Fetch all of the bots from the database which belong to the user; this is done by querying the User model, getting the UUID of the user, and then querying the Bot model for all bots with the same owner_id
    user = client.getIdTokenClaims()
    user = User.query.filter_by(email=user.email).first()
    if not user:
        return redirect("/logout")
    user = user.__dict__
    user.pop("_sa_instance_state")
    user["bots"] = Bot.query.filter_by(owner_id=user["id"]).all()
    return render_template("bots.html", user=user)

@web_logic.route("/bots/<uuid>")
async def bot(uuid):
    # Fetch the bot from the database using the UUID
    bot = Bot.query.filter_by(id=uuid).first()
    if not bot:
        return redirect("/bots")
    return render_template("bot.html", bot=bot)

@web_logic.route("/bots/<uuid>/edit")
async def edit_bot(uuid):
    flash("Bot editing is not implemented yet, coming soon!")
    return redirect("/bots")

@web_logic.route("/bots/<uuid>/delete")
async def delete_bot(uuid):
    # Check if the user is authenticated
    if not client.isAuthenticated():
        flash("You must be signed in to delete a bot.")
        return redirect("/bots")
    
    # Check if the user owns the bot
    user = client.getIdTokenClaims()
    user = User.query.filter_by(email=user.email).first()
    if not user:
        return redirect("/logout")
    user = user.__dict__
    user.pop("_sa_instance_state")

    # Fetch the bot from the database using the UUID
    bot = Bot.query.filter_by(id=uuid).first()
    if not bot:
        return redirect("/bots")
    if bot.owner_id != user["id"]:
        flash("You do not have permission to delete this bot.")
        return redirect("/bots")

    if not bot:
        return redirect("/bots")
    db.session.delete(bot)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if app.debug:
            return "Error: " + str(e)
        else:
            flash("An error occurred. Please try again later...")
            return redirect("/bots")
    return redirect("/bots")

@web_logic.route("/bots/new", methods=["POST", "GET"])
async def new_bot():
    if not client.isAuthenticated():
        flash("You must be signed in to create a bot.")
        return redirect("/")
    # Check if the request method is POST
    if request.method == "POST":
        # Get the user's email address
        user = client.getIdTokenClaims()
        user = User.query.filter_by(email=user.email).first()
        if not user:
            return redirect("/logout")
        user = user.__dict__
        user.pop("_sa_instance_state")
        # Get the bot's name, description, and binary file
        name = request.form.get("name")
        description = request.form.get("description", "")
        binary = request.files.get("binary")
        if not binary:
            flash("You must upload a binary file.")
            return redirect("/bots/new")
        # Read the binary file
        file_content = binary.read()
        
        # Check to see if it is an ELF file
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(file_content)
        if "application/x-sharedlib" not in file_type:
            flash("The file you uploaded is not a valid ELF file.")
            return redirect("/bots/new")

        # Create a new Bot object
        new_bot = Bot(
            name=name,
            description=description,
            binary=file_content,
            owner_id=user["id"],
        )

        new_leaderboard = Leaderboard(
            bot=new_bot,
        )

        # Add the new bot to the database
        db.session.add(new_bot)
        db.session.add(new_leaderboard)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if app.debug:
                return "Error: " + str(e)
            else:
                flash("An error occurred. Please try again later...")
                return redirect("/bots/new")
        return redirect("/bots")
    return render_template("new_bot.html")


@web_logic.route("/profile")
async def profile():
    if not client.isAuthenticated():
        return redirect("/sign-in")
    user = client.getIdTokenClaims()
    return render_template("profile.html", user=user)

@web_logic.route("/profile/edit")
async def edit_profile():
    flash("Profile editing is not implemented yet, coming soon!")
    return redirect("/profile")

@web_logic.route("/leaderboard")
async def leaderboard():
    flash("Leaderboard is not implemented yet, coming soon!")
    return redirect("/")

@web_logic.route("/privacy")
async def privacy_policy():
    flash("privacy is not implemented yet, coming soon!")
    return redirect("/")

@web_logic.route("/tos")
async def tos_policy():
    flash("TOS is not implemented yet, coming soon!")
    return redirect("/")

@web_logic.route("/conduct")
async def conduct():
    flash("Code of Conduct is not implemented yet, coming soon!")
    return redirect("/")

@web_logic.route("/api=docs")
async def api_docs():
    flash("API Docs are under construction, coming soon!")
    return redirect("/")

@web_logic.route("/callback")
async def callback():
    try:
        await client.handleSignInCallback(request.url)  # Handle a lot of stuff
        user = client.getIdTokenClaims()
        # Check if the user has an email address and an .edu email, if not, flash a message and redirect them to the home page
        if not user.email:
            flash("You must have an email address to sign in.")
            return redirect("/logout")
        if not user.email.endswith(".edu"):
            flash("You must have an .edu email address to sign in.")
            return redirect("/logout")

        if not User.query.filter_by(email=user.email).first():
            new_user = User(
                email=user.email,
            )
            db.session.add(new_user)

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if app.debug:
                    return "Error: " + str(e)
                else:
                    flash("An error occurred. Please try again later...")
                    return redirect("/logout")

        return redirect(
            "/"
        )  # Redirect the user to the home page after a successful sign-in
    except Exception as e:
        if app.debug:
            return "Error: " + str(e)
        else:
            flash("An error occurred. Please try again later...")
            return redirect("/logout")


@web_logic.route("/sign-in")
async def sign_in():
    # Get the sign-in URL and redirect the user to it
    if app.debug:
        return redirect(
            await client.signIn(
                redirectUri="https://dev-chess.iu.run/callback",
            )
        )
    else:
        return redirect(
            await client.signIn(
                redirectUri="https://chess.iu.run/callback",
            )
        )


@web_logic.route("/logout")
async def sign_out():
    if app.debug:
        return redirect(
            # Redirect the user to the home page after a successful sign-out
            await client.signOut(postLogoutRedirectUri="https://dev-chess.iu.run")
        )
    else:
        return redirect(
            # Redirect the user to the home page after a successful sign-out
            await client.signOut(postLogoutRedirectUri="https://chess.iu.run")
        )
