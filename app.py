# Import all required modules
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime, random
from datetime import datetime, time
import pytz

from helpers import login_required, lookup

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///journal.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Main menu
@app.route("/")
@login_required
def index():
    """Show main user page"""
    # Generate a random integer between 1-200 to display a random quote
    row = random.randint(1, 200)

    # Find today's date and time based on the NY timezone, using datetime and time modules
    tz_NY = pytz.timezone('America/New_York')
    now = datetime.now(tz_NY)
    now_time = now.time()

    # Print appropriate greeting based on if it's morning, afternoon, or evening
    if time(8, 00) <= now_time <= time(12, 00):
        greeting = "Good morning"
    if time(12, 00) <= now_time <= time(18, 00):
        greeting = "Good afternoon"
    else:
        greeting = "Good night"

    # Generate current time in the Hour:Minute format
    current_time = now.strftime("%H:%M")

    # Inspirational quotes from database: https://sharpquotes.com/download-45500-famous-motivational-quotes-database-in-excel-and-pdf/
    # Select random quote from the quotes database
    display_q = db.execute("SELECT quote FROM quotes WHERE id = ?", row)
    display_a = db.execute("SELECT author FROM quotes WHERE id = ?", row)

    # Get the user's name based on the current user_id,
    name = db.execute("SELECT name FROM users WHERE id = ?", session["user_id"])

    # Return the home page with the appropriate values for quote, author, greeting, and name as determined inside the function
    return render_template("index.html", quote=display_q[0]["quote"], author=display_a[0]["author"], greeting=greeting, time=current_time)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template('apology.html', message='must provide username')

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template('apology.html', message='must provide password')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template('apology.html', message='invalid username and/or password')

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return render_template('apology.html', message='must provide name')

        if not request.form.get("surname"):
            return render_template('apology.html', message='must provide last name')

        if not request.form.get("username"):
            return render_template('apology.html', message='must provide username')

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template('apology.html', message='must provide password')

        # Ensure that the confirmation field is filled
        elif not request.form.get("confirmation"):
            return render_template('apology.html', message='must provide password confirmation')

        # Ensure the two passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template('apology.html', message='two passwords do not match')

        # Store the password in a hash variable for security
        hash_password = generate_password_hash(request.form.get("password"))

        # Query database for username
        try:
            user = db.execute("INSERT INTO users (username, hash, name, surname) VALUES (?,?, ?, ?)", request.form.get("username"), hash_password, request.form.get("name"), request.form.get("surname"))
        except:
            return render_template('apology.html', message='username unavailable')

        session["user_id"] = user
        return redirect("/")  # Redirect user to home page

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user's password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template('apology.html', message='must provide username')

        # Ensure that the old password is provided
        elif not request.form.get("old_password"):
            return render_template('apology.html', message='must provide old password')

        # Get the id associated with the username entered by the user
        id = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        id_comp = id[0]["id"]

        # Ensure the username enters their own username and not someone else's
        if session["user_id"] != id_comp:
            return render_template('apology.html', message='username not valid')

        # Ensure that a new password is provided
        elif not request.form.get("new_password"):
            return apology("must provide new password", 400)
            return render_template('apology.html', message='must provide new password')

        # Ensure that the confirmation field is filled
        elif not request.form.get("confirmation"):
            return render_template('apology.html', message='must provide password new password confirmation')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return render_template('apology.html', message='invalid username and/or password')

        # Ensure the two passwords match
        if request.form.get("new_password") != request.form.get("confirmation"):
            return render_template('apology.html', message='two passwords do not match')

        # Store the password in a hash variable for security
        hash_password = generate_password_hash(request.form.get("new_password"))

        # Update users database, recording the new password
        db.execute("UPDATE users SET hash=? WHERE id =?", hash_password, session["user_id"])
        flash("Password changed successfully")  # Display success message

        return redirect("/")  # Redirect user to home page

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_password.html")


@app.route("/new_entry", methods=["GET", "POST"])
def new_entry():
    """Submit new journal entry"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # print the appropriate error messages if some or all of the required information is missing
        if not request.form.get("date"):
            return render_template('apology.html', message='must enter date')
        elif not request.form.get("prompt1"):
            return render_template('apology.html', message='must answer all prompts')
        elif not request.form.get("prompt2"):
            return render_template('apology.html', message='must answer all prompts')
        elif not request.form.get("prompt3"):
            return render_template('apology.html', message='must answer all prompts')
        elif not request.form.get("rating"):
            return render_template('apology.html', message='must answer all prompts')
        elif not request.form.get("extra"):
            return render_template('apology.html', message='must answer all prompts')
        elif not request.form.get("extra_ans"):
            return render_template('apology.html', message='must answer all prompts')

        # initialize useful variables using the information entered
        date = request.form.get("date")
        prompt1 = request.form.get("prompt1")
        prompt2 = request.form.get("prompt2")
        prompt3 = request.form.get("prompt3")
        extra = request.form.get("extra")
        extra_ans = request.form.get("extra_ans")
        rating = request.form.get("rating")

        # store all variables inside the entries SQL table, separating each of them based on the the columns they fall into
        new_entry = db.execute("INSERT INTO entries (date, prompt1, prompt2, prompt3, rating, user_id, extra, extra_ans) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", date, prompt1, prompt2, prompt3, rating, session["user_id"], extra, extra_ans)

        return redirect("/")  # Redirect to homepage after submitting entry

    else:
        return render_template("new_entry.html")  # If request via GET, redirect user to New Entry page


@app.route("/past_entries")
@login_required
def past_entries():
    """Show all past entries"""

    # Get all the information related to past entries in the entries database
    entries = db.execute("SELECT date, prompt1, prompt2, prompt3, extra, extra_ans, rating FROM entries WHERE user_id = ? ORDER BY date", session["user_id"])

    # If there are no past entries, print the appropriate error message
    if not entries:
        return render_template('apology.html', message='no diary entries')

    return render_template("past_entries.html", entries=entries) # Return the past entries page with entries as entries


@app.route("/calendar")
@login_required
def calendar():
    """Display my calendar with tasks"""

    # Return the Calendar page
    return render_template("calendar.html")


@app.route("/yale_calendar")
@login_required
def yale_calendar():
    """Display Yale's academic calendar"""

    # Get important dates and events for the fall semester
    fall = db.execute("SELECT date, event FROM fall")

    # Get important dates and events for the spring semester
    spring = db.execute("SELECT date, event FROM spring")

    # Return the Calendar page with fall as fall and spring as spring
    return render_template("yale_calendar.html", fall=fall, spring=spring)