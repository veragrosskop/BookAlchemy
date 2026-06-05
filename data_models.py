from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class Author(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(80), unique=True)
    birth_date: Mapped[date]
    date_of_death: Mapped[date | None]

    def __repr__(self):
        return f"<Author {self.name}>"

    def __str__(self):
        return f"{self.name}"


class Book(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(db.String(13), unique=True)
    author_id: Mapped[int] = mapped_column(db.ForeignKey("author.id"))
    title: Mapped[str] = mapped_column(db.String(100))
    publication_year: Mapped[int]

    def __repr__(self):
        return f"<Book {self.title}>"

    def __str__(self):
        return f"{self.title}"
