import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from helper import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")


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


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        # rows = db.execute(
         #   "SELECT * FROM users WHERE username = ?", request.form.get("username")
        #)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Check if the user has inputted username, password, and confirmation and that the password and confirmation match
    if request.method == "GET":
        return render_template("register.html")
    if not request.form.get("username"):
        return apology("missing username")
    elif not request.form.get("password"):
        return apology("missing password")
    elif not request.form.get("confirmation"):
        return apology("missing passowrd confirmation")
    elif request.form.get("confirmation") != request.form.get("password"):
        return apology("passwords don't match")
    # Try to insert username with the hashed password if not already taken by someone else
    try:
        db.execute("INSERT INTO users(username, hash) VALUES (?,?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password")))

    except ValueError:
        return apology("username taken")

    # Set unique session id
    session["user_id"] = db.execute(
        "SELECT id FROM users WHERE username = ?", request.form.get("username"))[0]["id"]

    # Flash the word registered to indicate user has successful registered
    flash("Registered")

    # Take user back to the login page
    return redirect("/login")


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
    

if __name__ == "__main__":
    app.run(debug=True)
