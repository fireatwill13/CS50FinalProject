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
    """Register user"""

    # Check if the user has inputted username, password, and confirmation and that the password and confirmation match
    if request.method == "GET":
        return render_template("register.html")
    
    first_name = request.form.get('first name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('pw')
    confirm_password = request.form.get('confirm pw')
    
    timezone = request.form.get("timezone")
    language = request.form.get("language")
    location = request.form.get("location")
    birthday = request.form.get("birthday")

    #check if the password matches confirm password
    if password != confirm_password:
        return apology("Passwords do not match")
    # Hash the password
    hashed_password = generate_password_hash(password)

    # Check if the email is already registered, returns id if exist, returns none if it does not exist
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        return "jinja part" #EDIT HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE
    
    try:
        with conn:
            conn.execute(
            "INSERT INTO users (username, password, email, timezone, language, location, birthday) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, hashed_password, email, timezone, language, location, birthday)
            ) #EDIT HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE HERE
    except sqlite3.IntegrityError:
        return apology("Error during registration")

    # Retrieve the user's ID
    
    # Log in the user
    session["user_id"] = user["id"]

    # Flash success message and redirect to login
    flash("Registered successfully")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #built in function for check password and hash password 
        username = request.form.get("username")
        password = request.form.get("password")

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username)
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
def index():
    """Show portfolio of stocks"""
    # select cash from users using the specific id tag that's generated when the user signs up; also to check if there are any missing users
    rows = db.execute("SELECT cash FROM users where id = ?", session["user_id"])
    if not rows:
        return apology("missing user")

    cash = rows[0]["cash"]
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as totalShares FROM transactions WHERE user_id = ? GROUP by symbol HAVING SUM(shares) > 0", session["user_id"])
    total = 0

    # Lookup stock and calculating total with the total shares times the price, both set to float
    for stock in stocks:
        stock_quote = lookup(stock["symbol"])
        total = float(stock["totalShares"]) * float(stock_quote["price"])
        if not stock_quote:
            # Skip this stock or handle the error
            return apology("Stock Doesn't Exist")
        stock["price"] = stock_quote["price"]
        stock["total"] = float(stock["totalShares"]) * stock["price"]

    # Display the Index html file for user, passing cash, stocks, and total as arguments for display
    return render_template("index.html", cash=cash, stocks=stocks, total=total)


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
