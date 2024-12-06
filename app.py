import os
import sqlite3

def get_db_connection():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database

conn = get_db_connection()


#Configure register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # Form data
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("pw")
    confirm_password = request.form.get("confirm_pw")
    timezone = request.form.get("timezone")
    language = request.form.get("language")
    location = request.form.get("country")
    birthday = request.form.get("birthday")

    # Validate passwords
    if password != confirm_password:
        return render_template("register.html", password_error="Passwords do not match")

    # Hash the password using pbkdf2:sha256
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # Database connection
    conn = get_db_connection()

    # Check if email or username already exists
    user_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user_email:
        return render_template("register.html", email_error="Email already exists")

    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        return render_template("register.html", username_error="Username already exists")

    # Insert user into database
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (first_name, last_name, username, password, email, timezone, language, location, birthday)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (first_name, last_name, username, hashed_password, email, timezone, language, location, birthday)
            )
    except sqlite3.IntegrityError:
        return render_template("register.html", general_error="Registration failed. Please try again.")

    # Retrieve the user's ID
    new_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    session["user_id"] = new_user["id"]

    # Flash success message
    flash("Registered successfully!")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Database connection
        conn = get_db_connection()

        # Get form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Query user by username
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        # Ensure user exists and password is correct
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error_message="Invalid username or password")

        # Remember which user has logged in
        session["user_id"] = user["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (e.g., clicking a link)
    return render_template("login.html")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def homepage():
    
    return render_template("friendship_homepage.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "GET":
        return render_template("buy.html")
    else:

        # CHeck if symbol exists and if user did indeed enter a symbol. Also check if the amount entered is valid (positive integer)
        if not request.form.get("symbol"):
            return apology("Please input a stock symbol")
        stockView = request.form.get("symbol")
        stockInformation = lookup(stockView)
        shares = request.form.get("shares")
        if not stockInformation:
            return apology("Invalid stock symbol")
        if not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("Please input a positive integer")
        # Declare and initiate variables to keep code more clean
        shares = int(shares)
        user_id = session["user_id"]
        price = stockInformation["price"]
        totalCost = shares*price

        tableRows = db.execute("SELECT cash FROM users where id = ?", user_id)

        # Get total for cash so code can compare the total cost to determine if the user has enough money
        cash = tableRows[0]["cash"]
        timeStamp = datetime.now()
        if totalCost > cash:
            return apology("NOT ENOUGH MONEY")

        # Update tables with cash substracted from buying stock
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", totalCost, user_id)

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (?, ?, ?, ?, ?)",
                   user_id, stockInformation["symbol"], shares, price, timeStamp)
        # Redirect user back to home page
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Format and set the history page with symbol, price, and timestamps using datetime that was included in buy and sell function
    stocks = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])
    for stock in stocks:
        stock_quote = lookup(stock["symbol"])
        stock["price"] = stock_quote["price"]
    # Display History HTML File
    return render_template("history.html", stocks=stocks)



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        # Display quote HTML
        return render_template("quote.html")

    else:
        # View the stock using the loopup function from helper and ensure that the stock is not empty and is valid
        stockView = request.form.get("symbol")
        stockInformation = lookup(stockView)
        if not stockView:
            return apology("Please enter a stock")
        elif not stockInformation:
            return apology("Invalid stock symbol")
        # Display quoted HTML, passing stockInformation as an argument
        return render_template("quoted.html", stockInformation=stockInformation)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session["user_id"]

    if request.method == "GET":
        # Select all symbols from transactions and pass it as an argument in the display of sell HTML
        symbolRows = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
        return render_template("sell.html", symbolRows=symbolRows)
    else:
        # Call the lookup helper function, view the stock and set the number of shares to float
        stockView = request.form.get("symbol")
        stockInformation = lookup(stockView)
        shares = float(request.form.get("shares"))
        rows = db.execute(
            "SELECT SUM(shares) as totalShares FROM transactions WHERE user_id = ? AND symbol = ?", user_id, stockView)
        # Ensure that the user has selected proper stocks or has inputted a valid positive integer or has enough shares to actually sell
        if not stockView:
            return apology("Select a Stock to Sell Please")

        if not shares or not shares.is_integer() or shares <= 0:
            return apology("Please input a postive integer of shares you wish to sell")

        if rows[0]["totalShares"] is None or rows[0]["totalShares"] < shares or len(rows) < 1:
            return apology("Not Enough Shares of Stocks")

        price = stockInformation["price"]
        totalMade = shares*price

        timeStamp = datetime.now()

        # Update the user's new cash amount after selling stock and insert it into the transactions table in SQL
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", totalMade, user_id)

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (?, ?, ?, ?, ?)",
                   user_id, stockInformation["symbol"], -1*shares, price, timeStamp)

        return redirect("/")


@app.route("/changePassword", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow user to change password"""
    if request.method == "GET":
        # Display the changePassword HTML
        return render_template("changePassword.html")

    else:
        # retrieve from OLD data
        currentPassword = request.form.get("currentPassword")
        newPassword = request.form.get("newPassword")
        confirmation = request.form.get("confirmation")

        # Validate the current and new password along with confirmation; ensure new password and confirmation matches
        if not currentPassword:
            return apology("Please enter current password")
        if not newPassword:
            return apology("Please enter new password")
        if not confirmation:
            return apology("Please confirm new password")
        if newPassword != confirmation:
            return apology("New passwords do not match")

        # Verify current password
        user_id = session["user_id"]

        # Update password in the database
        newPasswordHash = generate_password_hash(newPassword)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", newPasswordHash, user_id)
        # Flash to user that the password has been changed successfully
        flash("Password changed successfully!")
        # Redirect user back to home page
        return redirect("/")
    


conn.close()
if __name__ == "__main__":
    app.run(debug=True)

