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
from werkzeug.utils import secure_filename
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
    location = request.form.get("location")
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
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()  # Clear the session
    flash("You have been logged out successfully.", "success")
    return redirect("/login")  # Redirect to the login page



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
    




    friendship = conn.execute(
        "SELECT creator_id, recipient_id FROM friendships WHERE id = ?",
        (connection_id,)
    ).fetchone()

    if not friendship:
        flash("No such connection found.", "danger")
        return redirect("/")

    # Determine the recipient based on the logged-in user
    if session["user_id"] == friendship["creator_id"]:
        recipient_id = friendship["recipient_id"]
    elif session["user_id"] == friendship["recipient_id"]:
        recipient_id = friendship["creator_id"]
    else:
        flash("You are not part of this connection.", "danger")
        return redirect("/")

    # Fetch the recipient's country
    recipient_info = conn.execute(
        "SELECT location FROM users WHERE id = ?",
        (recipient_id,)
    ).fetchone()

    # Default to "Unknown" if no country is found
    recipient_country = recipient_info["location"] if recipient_info else "Unknown"



    # Fetch chat messages for the connection
    chat_messages = conn.execute(
        """
        SELECT cm.message_text, cm.timestamp, u.username AS sender
        FROM chat_messages cm
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.friendship_id = ?
        ORDER BY cm.timestamp ASC
        """,
        (connection_id,)
    ).fetchall()


    # Fetch existing events for the specified friendship connection
    events = conn.execute(
        "SELECT event_name, event_date FROM calendars WHERE friendship_id = ?",
        (connection_id,)
    ).fetchall()

    # Fetch images for the friendship
    images = conn.execute(
        "SELECT photo_url FROM images WHERE friendship_id = ?",
        (connection_id,)
    ).fetchall()


    # Fetch milestones for the friendship connection
    milestones = conn.execute(
        "SELECT id, milestone_name FROM milestones WHERE friendship_id = ?",
        (connection_id,)
    ).fetchall()

    # Handle adding a new event via POST request
    if request.method == "POST":
        event_name = request.form.get("event_details")
        event_date = request.form.get("event_date")

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
                flash("Event added successfully!", "success")
                return redirect(url_for('friendship_hub', connection_id=connection_id))
            except sqlite3.Error as e:
                flash(f"Error adding event: {e}", "danger")

    conn.close()

    return render_template("friendship_hub.html", connection_id=connection_id, chat_messages=chat_messages, recipient_country = recipient_country, events=events, images = images, milestones=milestones)

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
    

@app.route("/add-milestone/<int:connection_id>", methods=["POST"])
@login_required
def add_milestone(connection_id):
    milestone_text = request.form.get("milestone_text")

    # Validate the milestone length to be less than 20 characters
    if len(milestone_text) > 20:
        flash("Milestone must be less than 20 characters.", "danger")
        return redirect(url_for("friendship_hub", connection_id=connection_id))

    # Insert the milestone into the database
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO milestones (friendship_id, milestone_name)
                VALUES (?, ?)
                """,
                (connection_id, milestone_text)
            )
        flash("Milestone added successfully!", "success")
    except sqlite3.Error as e:
        flash(f"Error adding milestone: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("friendship_hub", connection_id=connection_id))


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload_image/<int:connection_id>", methods=["POST"])
@login_required
def upload_image(connection_id):
    # Check if file is in the request
    if 'image_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('friendship_hub', connection_id=connection_id))

    file = request.files['image_file']

    # Validate the file
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('friendship_hub', connection_id=connection_id))

    if file and allowed_file(file.filename):
        # Secure and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Store the image URL in the database
        photo_url = os.path.join('uploads', filename)  # Relative path
        conn = get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO images (friendship_id, photo_url)
                    VALUES (?, ?)
                    """,
                    (connection_id, photo_url)
                )
            flash("Image uploaded successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error uploading image: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for('friendship_hub', connection_id=connection_id))

    flash('Invalid file format. Only image files are allowed.', 'danger')
    return redirect(url_for('friendship_hub', connection_id=connection_id))


@app.route("/delete-milestone/<int:milestone_id>", methods=["POST"])
@login_required
def delete_milestone(milestone_id):
    """Delete a milestone by its ID."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
        flash("Milestone deleted successfully!", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting milestone: {e}", "danger")
    finally:
        conn.close()
    
    # Redirect back to the friendship hub
    return redirect(request.referrer or "/")

@app.route("/delete-photo/<int:friendship_id>", methods=["POST"])
@login_required
def delete_photo(friendship_id):
    """Delete a photo based on friendship_id and photo_url."""
    photo_url = request.form.get("photo_url")  # Get the photo URL from the form

    if not photo_url:
        flash("Photo URL is required for deletion.", "danger")
        return redirect(request.referrer or "/")

    conn = get_db_connection()
    try:
        # Check if the photo exists for the given friendship_id
        photo = conn.execute(
            "SELECT photo_url FROM images WHERE friendship_id = ? AND photo_url = ?",
            (friendship_id, photo_url)
        ).fetchone()

        if photo:
            # Build the full file path
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo["photo_url"])

            # Delete the photo file from the file system
            if os.path.exists(photo_path):
                os.remove(photo_path)

            # Delete the photo record from the database
            with conn:
                conn.execute(
                    "DELETE FROM images WHERE friendship_id = ? AND photo_url = ?",
                    (friendship_id, photo_url)
                )
            flash("Photo deleted successfully!", "success")
        else:
            flash("Photo not found for this friendship.", "danger")
    except sqlite3.Error as e:
        flash(f"Error deleting photo: {e}", "danger")
    finally:
        conn.close()

    # Redirect back to the friendship hub
    return redirect(request.referrer or "/")

@app.route("/send-message/<int:connection_id>", methods=["POST"])
@login_required
def send_message(connection_id):
    """Handle sending a chat message."""
    conn = get_db_connection()

    # Validate the friendship
    friendship = conn.execute(
        "SELECT creator_id, recipient_id FROM friendships WHERE id = ?",
        (connection_id,)
    ).fetchone()

    if not friendship:
        flash("No such connection found.", "danger")
        return redirect("/")

    # Ensure the user is part of the friendship
    if session["user_id"] not in (friendship["creator_id"], friendship["recipient_id"]):
        flash("You are not part of this connection.", "danger")
        return redirect("/")

    # Get the message text
    message_text = request.form.get("message_text")
    if not message_text:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("friendship_hub", connection_id=connection_id))

    # Insert the message into the database
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO chat_messages (friendship_id, sender_id, message_text)
                VALUES (?, ?, ?)
                """,
                (connection_id, session["user_id"], message_text)
            )
        flash("Message sent successfully!", "success")
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("friendship_hub", connection_id=connection_id))


conn = get_db_connection()
conn.close()
if __name__ == "__main__":
    app.run(debug=True)

