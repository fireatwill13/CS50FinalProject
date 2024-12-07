import os
import sqlite3
def get_db_connection():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn
from flask import Flask, flash, redirect, render_template, request, session, url_for
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

@app.route("/create-connection", methods=["POST"])
@login_required
def create_connection():
    """Create a new friendship connection."""
    conn = get_db_connection()
    creator_id = session["user_id"]
    creator_username = conn.execute(
        "SELECT username FROM users WHERE id = ?",
        (creator_id,)
    ).fetchone()["username"]

    # Get the recipient username from the form
    connection_name = request.form.get("connection_name")
    connections = conn.execute(
                """
                SELECT
                    id, 
                    CASE 
                        WHEN creator_id = ? THEN recipient_username 
                        ELSE creator_username 
                    END AS name, 
                    time_created 
                FROM friendships
                WHERE creator_id = ? OR recipient_id = ?
                ORDER BY time_created DESC
                """,
                (creator_id, creator_id, creator_id)
        ).fetchall()
    # Check if the connection name is provided
    if not connection_name:
        return render_template("friendship_homepage.html", connections=connections, connection_error="Please enter a connection name.")

    # Check if the recipient user exists
    recipient = conn.execute(
        "SELECT id, username FROM users WHERE username = ?",
        (connection_name,)
    ).fetchone()
    if connection_name == creator_username:
        return render_template("friendship_homepage.html", connections=connections, connection_error="You cannot create a connection with yourself.")

    if not recipient:
        return render_template("friendship_homepage.html", connections=connections, recipient_error="Username does not exist.")

    recipient_id = recipient["id"]
    recipient_username = recipient["username"]

    # Check if the friendship already exists
    existing_friendship = conn.execute(
        """
        SELECT * FROM friendships 
        WHERE (creator_id = ? AND recipient_id = ?) 
        OR (creator_id = ? AND recipient_id = ?)
        """,
        (creator_id, recipient_id, recipient_id, creator_id)
    ).fetchone()

    if existing_friendship:
        return render_template("friendship_homepage.html", connections=connections, friendship_error="Friendship already exists.")

    # Create the friendship
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO friendships (creator_id, creator_username, recipient_id, recipient_username)
                VALUES (?, ?, ?, ?)
                """,
                (creator_id, creator_username, recipient_id, recipient_username)
            )
        return render_template("friendship_homepage.html", connections=connections, confirmation_message="Friendship Successfully Created!")
    except sqlite3.IntegrityError:
        return redirect("/")

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
    conn = get_db_connection()

    user_id = session["user_id"]

    # Query friendships for the logged-in user
    connections = conn.execute(
        """
        SELECT
            id, -- include id of the actual friendship 
            CASE 
                WHEN creator_id = ? THEN recipient_username 
                ELSE creator_username 
            END AS name, 
            time_created 
        FROM friendships
        WHERE creator_id = ? OR recipient_id = ?
        ORDER BY time_created DESC
        """,
        (user_id, user_id, user_id)
    ).fetchall()

    conn.close()

    # Debug: Print connections
    print("Connections:", [dict(row) for row in connections])

    return render_template("friendship_homepage.html", connections=connections)


#Redirect to friendship_hub per the unique connection id from person

@app.route("/friendship_hub/<int:connection_id>", methods=["GET", "POST"])
@login_required
def friendship_hub(connection_id):
    conn = get_db_connection()

    # Fetch existing events for the specified friendship connection
    events = conn.execute(
        "SELECT event_name, event_date FROM calendars WHERE friendship_id = ?",
        (connection_id,)
    ).fetchall()

    # Handle adding a new event via POST request
    if request.method == "POST":
        event_name = request.form.get("event_details")
        event_date = request.form.get("event_date")

        print(f"Event Name: {event_name}, Event Date: {event_date}")  # Debugging

        # Insert new event into the database
        if event_name and event_date:
            try:
                with conn:
                    conn.execute(
                        """
                        INSERT INTO calendars (friendship_id, event_name, event_date)
                        VALUES (?, ?, ?)
                        """,
                        (connection_id, event_name, event_date)
                    )
                return redirect(url_for('friendship_hub', connection_id=connection_id))
            except sqlite3.Error as e:
                flash(f"Error adding event: {e}", "danger")
                print(f"Database error: {e}")  # Debugging

    # Close the connection after processing
    conn.close()

    # Return the friendship hub page with the events passed to Jinja
    return render_template("friendship_hub.html", connection_id=connection_id, events=events)



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
    

conn = get_db_connection()
conn.close()
if __name__ == "__main__":
    app.run(debug=True)

