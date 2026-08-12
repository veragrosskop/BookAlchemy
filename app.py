import datetime

from flask import Flask, render_template, request, flash, redirect, url_for
import os
from pathlib import Path

from sqlalchemy import select, asc, desc, or_

from data_models import db, Author, Book

app = Flask(__name__)

basedir = Path(__file__).resolve().parent
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{basedir / 'data' / 'library.sqlite'}"
db.init_app(app)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


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
            return render_template("add_author.html", form=request.form)
        existing_author = db.session.scalar(
            select(Author).where(Author.name == author_name)
        )
        if existing_author:
            flash(f"Author {author_name} already exists.", "error")
            return render_template("add_author.html", form=request.form)
        if not author_birth_date:
            flash("Author birth date is required.", "error")
            return render_template("add_author.html", form=request.form)
        try:
            author_birth_date = datetime.datetime.strptime(
                author_birth_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Date of birth must be in YYYY-MM-DD format.", "error")
            return render_template("add_author.html", form=request.form)
        if author_date_of_death:
            try:
                author_date_of_death = datetime.datetime.strptime(
                    author_date_of_death, "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Date of death must be in YYYY-MM-DD format.", "error")
                return render_template("add_author.html", form=request.form)
            if author_date_of_death < author_birth_date:
                flash("Date of death cannot be before date of birth.", "error")
                return render_template("add_author.html", form=request.form)
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


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """
    Adds a book to the database by retrieving information from the request form.
    :return:
    """
    authors = db.session.scalars(select(Author)).all()

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        title = request.form.get("title", "").strip()
        publication_year = request.form.get("publication_year", "").strip()
        author_id = request.form.get("author_id", "").strip()

        # validate book
        if not isbn:
            flash("ISBN is required.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)
        if len(isbn) != 13:
            flash("ISBN must be 13 digits.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)
        if not title:
            flash("Title is required.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        if not author_id:
            flash("Author is required.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        if not publication_year:
            flash("Publication year is required.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)
        try:
            publication_year = int(publication_year)
        except ValueError:
            flash("Publication year must be a number.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        author_birth_date = db.session.scalar(
            select(Author.birth_date).where(Author.id == author_id)
        )
        author_date_of_death = db.session.scalar(
            select(Author.date_of_death).where(Author.id == author_id)
        )
        if author_date_of_death and publication_year > author_date_of_death.year:
            flash("Book cannot be published after author's death.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)
        if author_birth_date and publication_year < author_birth_date.year:
            flash("Book cannot be published before author's birth.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        existing_book = db.session.scalar(select(Book).where(Book.isbn == isbn))
        if existing_book:
            flash("A book with this ISBN already exists.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        author = db.session.get(Author, int(author_id))
        if not author:
            flash("Selected author does not exist.", "error")
            return render_template("add_book.html", authors=authors, form=request.form)

        book = Book(
            isbn=isbn,
            title=title,
            publication_year=publication_year,
            author_id=author.id,
        )

        db.session.add(book)
        db.session.commit()

        flash(f"Book '{title}' added successfully!", "success")
        return redirect(url_for("add_book"))

    # GET request: show form
    authors = db.session.scalars(select(Author)).all()
    return render_template("add_book.html", authors=authors)


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """
    Detele a book from the database.
    :param book_id:
    :return:
    """
    book = db.session.get(Book, book_id)

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("index"))

    author = book.author
    db.session.delete(book)

    db.session.flush()
    if len(author.books) == 0:
        db.session.delete(author)
        db.session.flush()

    db.session.commit()

    flash(f"Book '{book.title}' deleted successfully.", "success")

    return redirect(url_for("index"))


@app.route("/", methods=["GET"])
def index():
    """
    Home page with search functionality and pagination.
    :return:
    """

    # sorting initialization
    sort = request.args.get("sort", "title")
    direction = request.args.get("direction", "asc")
    # pagination initialization
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)

    search = request.args.get("search", "").strip()
    query = select(Book).join(Author)

    if search:
        query = query.where(
            or_(
                Book.title.ilike(f"%{search}%"),
                Author.name.ilike(f"%{search}%"),
            )
        )

    # sort by column
    if sort == "author":
        column = Author.name
    elif sort == "year":
        column = Book.publication_year
    elif sort == "title":
        column = Book.title
    else:
        column = Book.title

    # direction ordering
    if direction == "desc":
        query = query.order_by(desc(column))
    elif direction == "asc":
        query = query.order_by(asc(column))
    else:
        query = query.order_by(asc(column))

    # pagination
    total_books = db.session.scalar(
        select(db.func.count()).select_from(query.subquery())
    )
    if total_books == 0 and search:
        flash("No books found for that search.", "error")
        return redirect(url_for("index"))

    books = db.session.scalars(
        query.limit(per_page).offset((page - 1) * per_page)
    ).all()
    total_pages = (total_books + per_page - 1) // per_page

    return render_template(
        "home.html",
        books=books,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        search=search,
    )


# # run only once
# with app.app_context():
#     db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
