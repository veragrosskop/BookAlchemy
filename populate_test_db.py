import json
from datetime import datetime

from app import app, db, Author, Book  # adjust import

TEST_JSON_PATH = "data/test_book_data.json"


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


with app.app_context():

    with open(TEST_JSON_PATH) as f:
        data = json.load(f)

    for item in data:

        author_data = item["author"]

        author = db.session.scalar(
            db.select(Author).where(Author.name == author_data["name"])
        )

        if not author:
            author = Author(
                name=author_data["name"],
                birth_date=parse_date(author_data["birth_date"]),
                date_of_death=None,
            )
            db.session.add(author)
            db.session.flush()

        book = Book(
            isbn=item["isbn"],
            title=item["title"],
            publication_year=item["publication_year"],
            author_id=author.id,
        )

        db.session.add(book)

    db.session.commit()

    print("Database seeded successfully!")
