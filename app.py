from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime
from email.message import EmailMessage
import smtplib
import os

from questions import QUESTIONS


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "study-assistant-development-secret-key"
)

database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///study_assistant.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = os.environ.get(
    "MAIL_SERVER",
    "smtp.gmail.com"
)

app.config["MAIL_PORT"] = int(
    os.environ.get(
        "MAIL_PORT",
        "587"
    )
)

app.config["MAIL_USERNAME"] = os.environ.get(
    "MAIL_USERNAME"
)

app.config["MAIL_PASSWORD"] = os.environ.get(
    "MAIL_PASSWORD"
)

app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
    "MAIL_DEFAULT_SENDER",
    app.config["MAIL_USERNAME"]
)


# ============================================================
# DATABASE
# ============================================================

db = SQLAlchemy(app)


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )


# ============================================================
# QUIZ HISTORY MODEL
# ============================================================

class QuizHistory(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    subject = db.Column(
        db.String(150),
        nullable=False
    )

    total_questions = db.Column(
        db.Integer,
        nullable=False
    )

    correct_answers = db.Column(
        db.Integer,
        nullable=False
    )

    incorrect_answers = db.Column(
        db.Integer,
        nullable=False
    )

    unanswered = db.Column(
        db.Integer,
        nullable=False
    )

    percentage = db.Column(
        db.Float,
        nullable=False
    )

    date_taken = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PASSWORD RESET SERIALIZER
# ============================================================

serializer = URLSafeTimedSerializer(
    app.config["SECRET_KEY"]
)


# ============================================================
# SEND PASSWORD RESET EMAIL
# ============================================================

def send_reset_email(recipient, reset_link):

    message = EmailMessage()

    message["Subject"] = "Study Assistant - Password Reset"

    message["From"] = app.config["MAIL_DEFAULT_SENDER"]

    message["To"] = recipient

    message.set_content(
        f"""
Hello,

You requested a password reset for your Study Assistant account.

Click the link below to create a new password:

{reset_link}

This password reset link will expire after 1 hour.

If you did not request a password reset, you can safely ignore this email.

Study Assistant
"""
    )

    with smtplib.SMTP(
        app.config["MAIL_SERVER"],
        app.config["MAIL_PORT"]
    ) as server:

        server.starttls()

        server.login(
            app.config["MAIL_USERNAME"],
            app.config["MAIL_PASSWORD"]
        )

        server.send_message(message)


# ============================================================
# HOME / DASHBOARD
# ============================================================

@app.route("/", endpoint="home")
@app.route("/", endpoint="index")
@login_required
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:
        return redirect(
            url_for("index")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill in all fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with that email already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(
                password
            )
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("index")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            login_user(user)

            flash(
                f"Welcome back, {user.name}!",
                "success"
            )

            return redirect(
                url_for("index")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            token = serializer.dumps(
                user.email,
                salt="password-reset"
            )

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            try:

                send_reset_email(
                    user.email,
                    reset_link
                )

                flash(
                    "If that email exists, a password reset link has been sent to your email.",
                    "success"
                )

            except Exception:

                app.logger.exception(
                    "Password reset email could not be sent."
                )

                flash(
                    "We could not send the password reset email right now. Please try again later.",
                    "error"
                )

        else:

            flash(
                "If that email exists, a password reset link has been sent to your email.",
                "success"
            )

    return render_template(
        "forgot_password.html"
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )

    except SignatureExpired:

        flash(
            "This password reset link has expired.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    except BadSignature:

        flash(
            "Invalid password reset link.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        flash(
            "User account not found.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not password:

            flash(
                "Please enter a new password.",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        user.password_hash = generate_password_hash(
            password
        )

        db.session.commit()

        flash(
            "Password successfully changed. Please log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html"
    )


# ============================================================
# SUBJECT PAGES
# ============================================================

@app.route("/ophthalmic")
@login_required
def ophthalmic():

    return render_template(
        "subjects/ophthalmic.html"
    )


@app.route("/ent")
@login_required
def ent():

    return render_template(
        "subjects/ent.html"
    )


@app.route("/oncology")
@login_required
def oncology():

    return render_template(
        "subjects/oncology.html"
    )


@app.route("/emergency")
@login_required
def emergency():

    return render_template(
        "subjects/emergency.html"
    )


@app.route("/research")
@login_required
def research():

    return render_template(
        "subjects/research.html"
    )


@app.route("/leadership1")
@login_required
def leadership1():

    return render_template(
        "subjects/leadership1.html"
    )


@app.route("/leadership2")
@login_required
def leadership2():

    return render_template(
        "subjects/leadership2.html"
    )


@app.route("/curriculum")
@login_required
def curriculum():

    return render_template(
        "subjects/curriculum.html"
    )


@app.route("/theatre")
@login_required
def theatre():

    return render_template(
        "subjects/theatre.html"
    )


# ============================================================
# MCQ PAGE
# ============================================================

@app.route("/mcqs")
@login_required
def mcqs():

    selected_subject = request.args.get(
        "subject",
        "all"
    ).strip()

    return render_template(
        "mcqs.html",
        questions=QUESTIONS,
        selected_subject=selected_subject
    )


# ============================================================
# SAVE QUIZ RESULT
# ============================================================

@app.route(
    "/save-quiz-result",
    methods=["POST"]
)
@login_required
def save_quiz_result():

    data = request.get_json(
        silent=True
    )

    if not data:

        return {
            "success": False,
            "message": "No quiz data received."
        }, 400

    history = QuizHistory(

        user_id=current_user.id,

        subject=data.get(
            "subject",
            "All Subjects"
        ),

        total_questions=int(
            data.get(
                "total_questions",
                0
            )
        ),

        correct_answers=int(
            data.get(
                "correct_answers",
                0
            )
        ),

        incorrect_answers=int(
            data.get(
                "incorrect_answers",
                0
            )
        ),

        unanswered=int(
            data.get(
                "unanswered",
                0
            )
        ),

        percentage=float(
            data.get(
                "percentage",
                0
            )
        ),

        date_taken=datetime.utcnow()
    )

    db.session.add(history)

    db.session.commit()

    return {
        "success": True
    }


# ============================================================
# QUIZ HISTORY PAGE
# ============================================================

@app.route("/history")
@login_required
def history():

    quiz_history = QuizHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(
        QuizHistory.date_taken.desc()
    ).all()

    total_quizzes = len(
        quiz_history
    )

    total_questions = sum(
        item.total_questions
        for item in quiz_history
    )

    total_correct = sum(
        item.correct_answers
        for item in quiz_history
    )

    if total_questions > 0:

        overall_percentage = round(
            (
                total_correct
                /
                total_questions
            ) * 100,
            1
        )

    else:

        overall_percentage = 0

    return render_template(
        "history.html",
        history=quiz_history,
        total_quizzes=total_quizzes,
        total_questions=total_questions,
        total_correct=total_correct,
        overall_percentage=overall_percentage
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )