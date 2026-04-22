from library.libraryConnection import connectToLibrary
from library.repositories.booksRepository import BooksRepository
from library.repositories.authorsRepository import AuthorsRepository
from library.repositories.bookshelfRepository import BookshelfRepository
import pandas as pd

class CSVimporter:
    def __init__(self, path):
        self.conn = connectToLibrary()
        self.path = path
        self.user_id = 1 #database should generate user id

    #TODO: accomodate for missing data
    def import_csv(self):
        books_repo = BooksRepository(self.conn)
        authors_repo = AuthorsRepository(self.conn)
        user_books_repo = BookshelfRepository(self.conn)

        df = pd.read_csv(self.path)

        for _, row in df.iterrows():
            work_id = str(row["Book Id"])
            title = row["Title"]
            isbn = row.get("ISBN")
            isbn13 = row.get("ISBN13")
            rating = row.get("My Rating")
            average_rating = row.get("Average Rating") #add to schema
            date_added = row.get("Date Added") #add to schema
            review = row.get("My Review")

            #book details - word, title, isbn, isbn13
            books_repo.insert_book(work_id, title, isbn=isbn, isbn13=isbn13)

            #book details - average rating
            #TODO: write logic to update rating update date and average rating

            #authors - author and additional authors
            authors = str(row.get("Author", "")).split(",")
            for a in authors:
                a = a.strip()
                if a:
                    author_id = authors_repo.get_or_create(a)

                    cur = self.conn.cursor()
                    cur.execute("""
                        INSERT INTO book_authors (work_id, author_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (work_id, author_id))
                    self.conn.commit()
                    cur.close()

            #user opinion - users rating and review of the book
            user_books_repo.upsert_user_book(
                self.user_id,
                work_id,
                rating = rating,
                date_added = date_added,
                review = review
            )

        self.conn.close()
        print("Import complete")