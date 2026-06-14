from src.models.book import Book
from database.library import Library

class BooksRepository:
    def __init__(self, library: Library):
        self.library = library

    def insertBook(self, work_id, title, subtitle=None, description=None, isbn10=None, isbn13=None):
        """add a book to the libary only if it's work_id does not already exist (to avoid dublicates)"""
        self.library.execute("""
            INSERT INTO books (work_id, title, subtitle, description, isbn10, isbn13)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (work_id) DO NOTHING;
        """, (work_id, title, subtitle, description, isbn10, isbn13))

    def updateBookRating(self, work_id, average_rating, rating_update_date):
        """If we have an average book rating from a more recent date, update the rating"""
        self.library.execute("""
            UPDATE books
            SET average_rating = %s, 
                rating_update_date = %s
            WHERE work_id = %s
            AND (
                rating_update_date IS NULL 
                OR rating_update_date < %s
            )
        """, (average_rating, rating_update_date, work_id, rating_update_date))
        self.library.commit()

    def updateBookTitle(self, work_id, title):
        self.library.execute("""
            UPDATE books
            SET title = %s
            WHERE work_id = %s;
        """, (title, work_id))
       

    def getAverageBookRating(self, work_id):
        result = self.library.fetchone("""
            SELECT average_rating
            FROM books
            WHERE work_id = %s;
        """, (work_id,))
        return result[0] if result else None

    def getBookByWorkID(self, work_id):
        result = self.library.fetchone("""
            SELECT * FROM books WHERE work_id = %s;
        """, (work_id,))
        return self.resultToBook(result) if result else None

    # TODO: Combine getBookByISBN10 and getBookByISBN13 into a single function that checks both fields, since some books may have one but not the other.
    def getBookByISBN10(self, isbn10):
        result = self.library.fetchone("""
            SELECT * FROM books WHERE isbn10 = %s;
        """, (isbn10,))
        return self.resultToBook(result) if result else None

    def getBookByISBN13(self, isbn13):
        result = self.library.fetchone("""
            SELECT * FROM books WHERE isbn13 = %s;
        """, (isbn13,))
        return self.resultToBook(result) if result else None

    #TODO combine getWorkIDByISBN10 and getWorkIDByISBN13 into a single function that checks both fields, since some books may have one but not the other.
    def getWorkIDByISBN10(self, isbn10):
        result = self.library.fetchone("""
            SELECT work_id FROM books WHERE isbn10 = %s;
        """, (isbn10,))
        return result[0] if result else None
    
    def getWorkIDByISBN13(self, isbn13):
        result = self.library.fetchone("""
            SELECT work_id FROM books WHERE isbn13 = %s;
        """, (isbn13,))
        return result[0] if result else None

    def getAllBooks(self):
        result = self.library.fetchall("""
            SELECT * FROM books;
        """)
        books = []
        for row in result:
            book = self.resultToBook(row)
            books.append(book)
        return books

    def resultToBook(self, result):
        if result is None:
            return None

        work_id = result[0]
        title = result[1]
        subtitle = result[2]
        description = result[3]
        isbn10 = result[4]
        isbn13 = result[5]
        average_rating = result[6]
        rating_update_date = result[7]
        rating_count = result[8]

        return Book(
            work_id,
            title,
            subtitle,
            description,
            isbn10,
            isbn13,
            average_rating,
            rating_update_date,
            rating_count,
        )
