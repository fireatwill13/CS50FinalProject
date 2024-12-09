# Continental Central

**Continental Central** is a web-based application designed to organize personal connections. The platform allows users to track and create friendships, chat in real time, share achievements, and explore different cultures related to their friends’ locations. This document outlines the overall structure and implementation rationale that go behind the making of this application.

GitHub Link: https://github.com/fireatwill13/CS50FinalProject.git

Video Link: https://www.youtube.com/watch?v=m7D7CWBrB9k


---

Prerequisites
-------------

Make sure you have the following installed on your system:

-   **Python 3.0 or later**

    -   [Download Python](https://www.python.org/downloads/)
-   **pip3 (Python Package Installer)**

    -   Comes pre-installed with Python. If not, follow [this guide](https://pip.pypa.io/en/stable/installation/).

* * * * *

Required Libraries and Modules
------------------------------

The following libraries and modules are used in the project. Use the commands provided to install them.

### Built-in Python Modules

These modules come pre-installed with Python and require no additional action:

-   `os`
-   `sqlite3`
-   `json`
-   `datetime`

* * * * *

### Third-party Libraries

Install the following dependencies:

1.  **Flask**

    -   Framework for building web applications.

    `pip install Flask`

2.  **Flask-Session**

    -   Enables server-side session management.

    `pip install Flask-Session`

3.  **Werkzeug**

    -   Provides utilities like password hashing and file security.

    `pip install Werkzeug`

4.  **pytz**

    -   Handles time zones.

    `pip install pytz`

* * * * *

Installation Instructions
-------------------------

1.  Clone the Repository:

    `git clone https://github.com/your-username/friendship-hub.git
    cd friendship-hub`

2.  Create a Virtual Environment (Optional but Recommended):

    `python -m venv venv
    source venv/bin/activate   # For macOS/Linux
    venv\Scripts\activate      # For Windows`

3.  Install Dependencies: Use the provided `requirements.txt` file to install all required libraries.

    `pip install -r requirements.txt`

    If `requirements.txt` is not available, manually install the libraries as outlined above.

4.  Create the Database: Use the provided database schema or initialize the database file:

    `sqlite3 data.db < schema.sql`

    If `schema.sql` is not available, ensure a `data.db` file exists, and your application handles table creation on first run.

5.  Run the Application: Start the Flask development server:

    `flask run`

6.  Access the Application: Open your browser and navigate to:

    `http://127.0.0.1:5000`

**1. If the program returns an error, it is likely because a required program is not installed.**

**2. You might get an libSSL warning, just click ignore warning to bypass it**

## Features

### Friendship Hub
- Create and view records of friendships.
- Organize friendships with timestamps.

### Shared Calendar
- Plan events collaboratively with your friends.

### Real-Time Texting
- Send and receive messages asynchronously in a chat window.

### Photo Gallery
- Share and view images within friendship hubs.
- Zoom into shared images and manage uploads.

### Translate
- Translate webpage into your preferred language.
- Designed using translation API.

### Culture
- Explore population, regions, languages, and history based on your friends’ locations.

### Maps
- Display and search locations with an integrated map API.

### Secure User Accounts
- Register and log in with password hashing and session management.

---

## Structure

### Key Files and Directories

- **`app.py`**: Main backend script managing routes and logic.
- **`templates/`**: Contains HTML templates for dynamic rendering using Flask's Jinja2.
  - `friendship_homepage.html`: Dashboard to manage friendships.
  - `friendship_hub.html`: Detailed friendship interface.
  - `login.html`: User login page.
  - `register.html`: User registration page.
- **`static/`**: Stores static assets (CSS, JavaScript, images).
- **`hashlibverification.py`**: Handles secure password hashing and verification.
- **`testsql.sql`**: SQL script for initializing the SQLite database.

---

## How to Use

### 1. Login
- Visit the login page and enter your username and password to access the application.
- If you don’t have an account, click on the **Register** button.

### 2. Register
- Navigate to the `/register` endpoint to create an account.
- Fill in the required details: name, username, email, password, country, time zone, language, and homepage.
- Choose a secure password; it will be hashed and stored securely.

### 3. Homepage
- View all existing friendships.
- Check the **Recent Updates** section for updates (e.g., messages, milestones, events).
- Use the **Create New Connection** button to add friendships to the friendship hub.
  - Enter the username of the person you want to connect with.

### 4. Friendship Hub
Each Friendship Hub offers:

#### Shared Calendar
- Add and view events specific to the friendship.
  - **To create a new event**:
    1. Enter event details in the first text box.
    2. Enter the event date in `yy-mm-dd` format in the second box.

#### Photo Gallery
- Upload and manage shared photos.
  - **To upload a new photo**:
    - Use the **Upload Image** button to add a photo to the album.
  - **To delete a photo**:
    - Click the red **X** next to the photo you want to delete.

#### Chat
- Talk with friends in real time.
  - **To send a message**:
    - Enter your message in the text box and click the **Send** button.

```javascript
// Example: Polling for new messages
function fetchMessages() {
    fetch('/api/messages')
        .then(response => response.json())
        .then(data => {
            displayMessages(data);  // Function to update the UI
        });
}
setInterval(fetchMessages, 3000);  // Poll every 3 seconds
```

### Cultural Information
- Scroll through **Culture Overview** to learn about your friend’s country’s culture and history.

### Maps
- Explore your friend’s location virtually.
  - Enter your friend’s address and see it pinpointed on the map.
  - Zoom in or out to explore adjacent areas.

<video src="map.mov" width="320" height="240" controls></video>

---

### Security Features

#### Password Hashing
- User passwords are hashed with secure algorithms using `hashlib` to prevent raw storage.

#### Session Management
- Flask session management securely tracks authenticated users.

#### CSRF Protection
- Forms are protected against cross-site request forgery attacks.

---

### FAQs

**How is my data protected?**
- User data is stored in a secure SQLite database. Passwords are hashed to prevent unauthorized access.

**Can I add multiple events for the same date?**
- Yes, the Shared Calendar allows multiple events to be added for any date.

**What map services are used?**
- The application integrates `Leaflet.js` and `OpenStreetMap` for its mapping functionality.

---

### 🛠️ Known Limitations

#### Polling for Chat
- The chat system uses polling for real-time updates, which can introduce slight delays. Future updates may implement WebSocket-based chat for improved performance.

#### Mobile Responsiveness
- While the application is mobile-friendly, some features, like map interactions, are better experienced on larger screens.
