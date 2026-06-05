import datetime

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy, query
import os

from sqlalchemy import select

from data_models import db, Author, Book

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
)
db.init_app(app)
app.config["SECRET_KEY"] = "your-secret-key"


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """
    This route allows the user to add an author to the database.
    On Get request, it renders the add_author.html template.
    On Post request, it adds the author to the database and displays a success message.

    :return:
    """
    if request.method == "GET":
        return render_template("add_author.html")
    if request.method == "POST":
        author_name = request.form.get("name")
        author_birth_date = request.form.get("birthdate")
        author_date_of_death = request.form.get("date_of_death")

        # validate author
        if not author_name:
            flash("Author name is required.", "error")
            return render_template(
                "add_author.html",
                name=author_name,
                birthdate=request.form.get("birthdate"),
                date_of_death=request.form.get("date_of_death"),
            )
        existing_author = db.session.scalar(
            select(Author).where(Author.name == author_name)
        )
        if existing_author:
            flash(f"Author {author_name} already exists.", "error")
            return render_template(
                "add_author.html",
                name=author_name,
                birthdate=request.form.get("birthdate"),
                date_of_death=request.form.get("date_of_death"),
            )
        if not author_birth_date:
            flash("Author birth date is required.", "error")
            return render_template(
                "add_author.html",
                name=author_name,
                birthdate=request.form.get("birthdate"),
                date_of_death=request.form.get("date_of_death"),
            )
        try:
            author_birth_date = datetime.datetime.strptime(
                author_birth_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Date of birth must be in YYYY-MM-DD format.", "error")
            return render_template(
                "add_author.html",
                name=author_name,
                birthdate=request.form.get("birthdate"),
                date_of_death=request.form.get("date_of_death"),
            )
        if author_date_of_death:
            try:
                author_date_of_death = datetime.datetime.strptime(
                    author_date_of_death, "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Date of death must be in YYYY-MM-DD format.", "error")
                return render_template(
                    "add_author.html",
                    name=author_name,
                    birthdate=request.form.get("birthdate"),
                    date_of_death=request.form.get("date_of_death"),
                )
            if author_date_of_death < author_birth_date:
                flash("Date of death cannot be before date of birth.", "error")
                return render_template(
                    "add_author.html",
                    name=author_name,
                    birthdate=request.form.get("birthdate"),
                    date_of_death=request.form.get("date_of_death"),
                )
        else:
            author_date_of_death = None

        author = Author(
            name=author_name,
            birth_date=author_birth_date,
            date_of_death=author_date_of_death,
        )
        db.session.add(author)
        db.session.commit()

        flash(f"Author {author_name} added successfully!", "success")
        return redirect(url_for("add_author"))
    return render_template("add_author.html")


# # run only once
# with app.app_context():
#   db.create_all()
