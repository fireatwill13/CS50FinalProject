Continental Central
----------------

**Continental Central** is a web-based application designed to organize personal connections. The platform allows users to track and create friendships, chat in real time, share achievements, and explore different cultures related to their friends' locations. This document outlines the overall structure and implementation rationale that go behind the making of this application.

* * * * *

Structure
---------

Continental Central is a full-stack web application using Python with Flask as the backend framework, HTML/CSS/JavaScript for the front end, and SQLite for persistent data storage. The application follows a modular design, which distinguishes between authentication, data management, and the user interface.

Authentication: Manages user registration, login, and session handling.

Data Management: Handles relationships, messaging, event calendars, and media uploads.

User Interface: Provides a responsive design for real-time interaction.

* * * * *

### Backend

1.  Flask Framework

-   Flask was chosen because it is simple and flexible. It integrates well with SQLite and Jinja templates, which allows for dynamic content rendering.

3.  Database: SQLite

-   SQLite was selected for its lightweight and serverless nature. It suits the needs of this project, which focuses on personal data storage rather than a large-scale deployment.

-   Database schema includes:

-   Users table (for authentication and profile information)

-   Connections table (to store friendship details)

-   Messages table (for real-time chat)

-   Events table (for shared calendar)

-   Photos table (to manage photo uploads and metadata)

-   SQL queries for managing these entities are encapsulated in testsql.sql for easy maintenance and debugging.

5.  Security

-   Passwords are hashed using hashlib with a secure hashing algorithm. The hashlibverification.py script ensures robust password storage.

-   CSRF protection is implemented using Flask-WTF, ensuring all forms are secure from malicious inputs.

* * * * *

### Frontend

1.  **HTML Templates**

-   friendship_homepage.html, friendship_hub.html, , and register.html make up the modular front-end components:

-   login.html allows users to log in using their username and password.

-   register.html asks the users for their first name,last name, desired username, email, password, time zone, country, preferred language, and birthday to create a new account.

-   friendship_homepage.html displays the user's current time and location, as well as recent updates from their connections. The page also allows users to create new connections by entering their friends' usernames.

-   friendship_hub.html displays the users' current time and location, milestones with their friends, as well as photos and calendar events shared with their friends. It also includes a text interface and a cultural information section that allows users to learn about their friend's culture. 

1.  **CSS**

-   Custom styling is applied using linked CSS files (/static/styles.css) to enhance the visual appeal. Bootstrap 5.3 is integrated for responsive and consistent design.

3.  **JavaScript**

-   Real-time interactions are managed using JavaScript, including:

-   Clock updates (updateClock() function).

-   Fetching and displaying updates (loadRecentUpdates()).

-   Dynamic map interactions using Leaflet.js and OpenStreetMap tiles.

-   Chat functionality that handles asynchronous message sending and receiving.

4. **API**

- **Google Map API** is used to pinpoint user location on a real-time basis.

- **Wikipedia API & REST Countries API** are used to fetch cultural information about specfic countries to generate a brief introduction to that country.

- **Google Translate API** is implemented to translate all webpages into different languages, in order to suit the demand of the users. 

* * * * *

### Key Features and Design Decisions

1.  Friendship Hub

-   Displays all connections in a list format, including creation timestamps. New connections can be added via a form.

-   Error messages for failed connection creation are displayed using Flask's flash messaging.

3.  Shared Calendar

-   Events are added dynamically to the calendar using a form. Events are stored in the database and retrieved for rendering.

5.  Photo Gallery

-   Users can upload images, which are stored on the server. Images are displayed in a responsive gallery. A modal is implemented for image zoom functionality.

7.  Chat System

-   A simple, asynchronous chat system was implemented using Flask routes. Messages are stored in the database and fetched for display.

9.  Cultural Information

-   Fetches data from external APIs like REST Countries and Wikipedia to provide insights into a friend's location.

-   A collapsible navbar displays cultural details such as traditional food, landmarks, and festivals.

* * * * *

### Design Challenges

1.  API Implementation

-   Integrating the REST Countries API required additional logic to handle edge cases like missing or inconsistent data formats. 

-   The Wikipedia API occasionally returned non-standard responses, requiring fallback mechanisms.

-   APIs like Leaflet requires additional styling for it to be displayed properly. 

3.  Real-Time Features

-   Real-time chat and updates are challenging in state management. It is difficult to make sure that both the sender and recipient get the text on time. It also took us a lot of time making sure that the SQL matches up with the code. 

5.  Cross-Browser Compatibility

-   Ensuring the application works the same across browsers, especially for responsive design elements.

* * * * *

### Lessons Learned

1.  Modular Design

-   Adopting Flask's blueprint system could further modularize application features, making the project easier to scale.

3.  Testing

-   Automated testing frameworks like PyTest should be integrated for more robust backend validation.

-   Frontend testing with Selenium could be used to verify UI consistency.

* * * * *

### Future Enhancements

1.  WebSocket Integration

-   Replacing the current polling-based chat system with WebSockets for real-time communication.

3.  Mobile Application

-   Creating a mobile app version of the Continental Central using a framework like Flutter.

5.  Enhanced Analytics

-   Adding insights into friendship activity using a dashboard with visualizations like graphs and timelines.