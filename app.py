import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, url_for, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///enemylist.db")

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    enemies = db.execute("SELECT name, reason FROM enemies WHERE enemy_id=? ORDER BY name", session["user_id"])
    print(enemies)
    return render_template("index.html", enemies=enemies)
        
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        if not request.form.get("name"):
            return redirect(url_for("index"))

        # Ensure password was submitted
        elif not request.form.get("reason"):
            return redirect(url_for("index"))
            
        db.execute("INSERT INTO enemies (name, reason, enemy_id) VALUES (?, ?, ?)", request.form.get("name"), request.form.get("reason"), session["user_id"])
        
        return redirect(url_for("index"))
    else:
        return render_template("add.html")
        
@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        if not request.form.get("name"):
            return redirect(url_for("delete"))
            
        rows = db.execute("SELECT * FROM enemies WHERE name = ? AND enemy_id = ?", request.form.get("name"), session["user_id"])

        if len(rows) < 1:
            errorMessage = "Cannot Find Such Enemy"
            return render_template("delete.html", errorMessage=errorMessage)
            
        db.execute("DELETE FROM enemies WHERE enemy_id=? AND name=?", session["user_id"], request.form.get("name"))
        
        return redirect(url_for("index"))
    else:
        return render_template("delete.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            errorMessage = "Must Have A Username"
            return render_template("login.html", errorMessage=errorMessage)

        # Ensure password was submitted
        elif not request.form.get("password"):
            errorMessage = "Must Have A Password"
            return render_template("login.html", errorMessage=errorMessage)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            errorMessage = "Password Or Username Is Incorrect"
            return render_template("login.html", errorMessage=errorMessage)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return  redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    errorMessage = ""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            errorMessage="Must Have A Username"
            return render_template("register.html", errorMessage=errorMessage)

        # Ensure password was submitted
        elif not request.form.get("password"):
            errorMessage="Must Have A Password"
            return render_template("register.html", errorMessage=errorMessage)

        # Ensure confirmation of the password was submitted
        elif not request.form.get("confirmation"):
            errorMessage="Must Confirm Your Password"
            return render_template("register.html", errorMessage=errorMessage)

        Rpassword = request.form.get("password")
        Repassword = request.form.get("confirmation")
        Rusername = request.form.get("username")

        if (Rpassword != Repassword):
            errorMessage="Passwords Doesn't Match"
            return render_template("register.html", errorMessage=errorMessage)

        rowsR = db.execute("SELECT * FROM users WHERE username = ?", Rusername)
        print(rowsR)

        if len(rowsR) != 0:
            errorMessage="Invalid Username, Please Choose Another"
            return render_template("register.html", errorMessage=errorMessage)
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", Rusername, generate_password_hash(Rpassword))

        return redirect(url_for("index"))
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("index"))
    
@app.route("/origin")
@login_required
def origin():
    return render_template("origin.html")
    
