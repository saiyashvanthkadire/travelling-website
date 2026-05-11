import os
from functools import wraps

import mysql.connector
from mysql.connector import Error

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__, template_folder="template")
app.secret_key = "change-this-secret-key"


# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "add-your-password",
    "database": "aeroquest",
}


# MySQL Connection
def get_connection(include_database=True):
    config = DB_CONFIG.copy()

    if not include_database:
        config.pop("database", None)

    return mysql.connector.connect(**config)


# Create Database and Tables Automatically
def init_db():
    try:
        # Create database
        connection = get_connection(include_database=False)
        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )

        cursor.close()
        connection.close()

        # Create tables
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(80) NOT NULL,
                last_name VARCHAR(80) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                destination VARCHAR(255) NOT NULL,
                travel_date VARCHAR(50) NOT NULL,
                guests INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()
        cursor.close()
        connection.close()

        print("Database and tables created successfully.")

    except Error as exc:
        print(f"MySQL setup failed: {exc}")


# Login Required Decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login_page"))

        return view(*args, **kwargs)

    return wrapped_view


# Default Route
@app.route("/")
def index():
    return redirect(url_for("login_page"))


# Login Page
@app.route("/login.html")
def login_page():
    return render_template("login.html")


# Signup Route
@app.route("/signup", methods=["POST"])
def signup():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not first_name or not last_name or not email or not password or not confirm_password:
        flash("Please fill all signup fields.", "error")
        return redirect(url_for("login_page"))

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("login_page"))

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (first_name, last_name, email, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (
            first_name,
            last_name,
            email,
            generate_password_hash(password)
        ))

        connection.commit()
        user_id = cursor.lastrowid

        cursor.close()
        connection.close()

        session["user_id"] = user_id
        session["user_name"] = f"{first_name} {last_name}"
        session["user_email"] = email

        flash("Account created successfully.", "success")
        return redirect(url_for("homepage"))

    except mysql.connector.IntegrityError:
        flash("Email already exists. Please login.", "error")

    except Error as exc:
        flash(f"Database error: {exc}", "error")

    return redirect(url_for("login_page"))


# Login Route
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter email and password.", "error")
        return redirect(url_for("login_page"))

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

    except Error as exc:
        flash(f"Database error: {exc}", "error")
        return redirect(url_for("login_page"))

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["user_name"] = f"{user['first_name']} {user['last_name']}"
        session["user_email"] = user["email"]

        flash("Login successful.", "success")
        return redirect(url_for("homepage"))

    flash("Invalid email or password.", "error")
    return redirect(url_for("login_page"))


# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login_page"))


# Homepage
@app.route("/homepage.html")
@login_required
def homepage():
    return render_template("homepage.html")


# Destination Page
@app.route("/destination.html")
@login_required
def destination():
    return render_template("destination.html")


# Packages Page
@app.route("/packages.html")
@login_required
def packages():
    return render_template("packages.html")


# Booking Form Page
@app.route("/Bookingform.html")
@login_required
def booking_form():
    return render_template("Bookingform.html")


# Store Booking Data in MySQL
@app.route("/book", methods=["POST"])
@login_required
def book():
    destination = request.form.get("destination", "").strip()
    travel_date = request.form.get("travel_date", "").strip()
    guests = request.form.get("guests", "").strip()

    if not destination or not travel_date or not guests:
        flash("Please fill all booking fields.", "error")
        return redirect(url_for("booking_form"))

    try:
        guests = int(guests)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO bookings (user_id, destination, travel_date, guests)
            VALUES (%s, %s, %s, %s)
        """, (
            session.get("user_id"),
            destination,
            travel_date,
            guests
        ))

        connection.commit()
        cursor.close()
        connection.close()

        flash("Booking submitted successfully!", "success")

    except ValueError:
        flash("Guests must be a number.", "error")

    except Error as exc:
        flash(f"Database error: {exc}", "error")

    return redirect(url_for("booking_form"))


# Contact Page
@app.route("/contact.html")
@login_required
def contact():
    return render_template("contact.html")


# Store Contact Data in MySQL
@app.route("/contact_submit", methods=["POST"])
@login_required
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill all contact fields.", "error")
        return redirect(url_for("contact"))

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO contacts (name, email, message)
            VALUES (%s, %s, %s)
        """, (
            name,
            email,
            message
        ))

        connection.commit()
        cursor.close()
        connection.close()

        flash("Your message has been sent successfully!", "success")

    except Error as exc:
        flash(f"Database error: {exc}", "error")

    return redirect(url_for("contact"))


# Run App
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
