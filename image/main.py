from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import imageio.v2 as imageio
from datetime import timedelta
import os
import cv2
import numpy as np
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vishalchoudharyiitian1@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'stig zuyc xmwa wkny'  # Change this (Use App Password if 2FA is enabled)
app.config['MAIL_DEFAULT_SENDER'] = 'vishalchoudharyiitian1@gmail.com'

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(100), nullable=False)


# Create database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    print(f"The operation is {operation} and filename is {filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    newfilename = f"static/{filename.split('.')[0]}"
    
    try:
        img = imageio.imread(filepath)
        if img is None:
            raise ValueError("Error loading image!")
    except Exception as e:
        flash(f"Error processing image: {str(e)}", "danger")
        return None

    match operation:
        case "cgray":
            imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newfilename += ".png"
        case "cwebp":
            newfilename += ".webp"
        case "cjpg":
            newfilename += ".jpg"
        case "cpng":
            newfilename += ".png"
        case "cbmp":
            newfilename += ".bmp"
        case "ctiff":
            newfilename += ".tiff"
        case "cresized":
            imgProcessed = cv2.resize(img, (300, 300))
            newfilename += "_resized.png"
        case "rotate":
            imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            newfilename += "_rotated.png"
        case "flip":
            imgProcessed = cv2.flip(img, 1)
            newfilename += "_flipped.png"
        case "cgif":
            newfilename += ".gif"
            imageio.mimsave(newfilename, [img], duration=0.5)
            return newfilename
        case "cpdf":
            newfilename += ".pdf"
            Image.fromarray(img).save(newfilename, "PDF")
            return newfilename
        case "cheic":
            newfilename += ".heic"
        case "capng":
            newfilename += ".apng"
        case "cico":
            newfilename += ".ico"
        case "craw":
            newfilename += ".raw"
        case "cdng":
            newfilename += ".dng"
        case "cexr":
            newfilename += ".exr"
        case "chdr":
            newfilename += ".hdr"
        case _:
            flash("Invalid operation!")
            return None
    
    imageio.imwrite(newfilename, imgProcessed if 'imgProcessed' in locals() else img)
    return newfilename
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("how.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not username or not email or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for("contact"))

        # Save message in the Contect model
        new_message = Contact(username=username, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template('contact.html')

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.")
            return redirect(url_for("login"))
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            flash(f"Login successful! Welcome, {session['username']}", "success")
            print("Session data:", session)  # Debugging line to check session values
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully.")   
    return redirect(url_for("home"))

# Forgot Password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt='password-reset')
            reset_link = url_for("reset_password", token=token, _external=True)

            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_link}\nThis link expires in 30 minutes."
            mail.send(msg)

            flash("A password reset link has been sent to your email.", "info")
        else:
            flash("Email not found!", "danger")

    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=1800)
    except:
        flash("The reset link is invalid or expired.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = generate_password_hash(request.form["password"])
        user = User.query.filter_by(email=email).first()

        if user:
            user.password = new_password
            db.session.commit()
            flash("Password has been reset. You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "user_id" not in session:
        flash("You must sign up or log in first!", "danger")
        return redirect(url_for("login"))  
    
    if request.method == "POST":
        operation = request.form.get("operation")
        
        if 'file' not in request.files:
            flash('No file part', "danger")
            return redirect(url_for("edit"))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', "danger")
            return redirect(url_for("edit"))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            processed_filepath = processImage(filename, operation)
            if processed_filepath:
                flash(f"Your image has been processed and is available below.", "success")
                return render_template("index.html", processed_image=processed_filepath)
    
    return render_template("index.html")


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)  