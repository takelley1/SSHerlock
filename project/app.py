import os

from flask import Flask, render_template_string, render_template, redirect, url_for, request, flash
from flask_security import Security, current_user, auth_required, SQLAlchemySessionUserDatastore, hash_password, login_user
from database import db_session, init_db
from models import User, Role
import logging as log

log.basicConfig(format="%(asctime)s %(funcName)s: %(message)s", level="INFO")

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True

# Generate a nice key using secrets.token_urlsafe()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')
app.config["PASSWORD_COMPLEXITY_CHECKER"] = "zxcvbn"

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
app.security = Security(app, user_datastore)

# Views
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_post():
    # code to validate and add user to database goes here
    email = request.form.get("email")
    name = request.form.get("name")
    password = request.form.get("password")

    user = User.query.filter_by(
        email=email
    ).first()  # if this returns a user, then the email already exists in database

    # if a user is found, we want to redirect back to signup page so user can try again
    if user:
        flash("Email address already exists")
        return redirect(url_for("signup"))

    # add the new user to the database
    user = user_datastore.create_user(email=email, password=hash_password(password))
    user_datastore.commit()
    login_user(user, remember=False)

    return redirect(url_for("profile"))

# @app.route("/login")
# def login():

#     email = request.form.get("email")
#     password = request.form.get("password")
#     user = user_datastore.find_user(email=email)

#     login_user(user, remember=False)
#     return render_template("security/login_user.html")

# @app.route("/login", methods=["POST"])
# def login():
#     return render_template("security/login_user.html")

@app.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html", name=current_user.email)

# one time setup
with app.app_context():
    # Create a user to test with
    init_db()
    if not app.security.datastore.find_user(email="test@me.com"):
        app.security.datastore.create_user(email="test@me.com", password=hash_password("password"))
    db_session.commit()

if __name__ == '__main__':
    # run application (can also use flask run)
    app.run()