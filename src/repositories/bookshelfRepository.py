from src.database.repositories.booksRepository import BooksRepository
from src.dtos.book import Book

class BookshelfRepository:
    def __init__(self, conn):
        self.conn = conn

    def upsertBookIntoUserBookshelf(self, user_id, work_id, rating=None, date_added=None, review=None, read_count=None, shelf=None):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO user_books (user_id, work_id, rating, date_added, review, read_count, shelf)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, work_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                date_added = EXCLUDED.date_added,
                review = EXCLUDED.review,
                read_count = EXCLUDED.read_count,
                shelf = EXCLUDED.shelf;
        """, (user_id, work_id, rating, date_added, review, read_count, shelf))
        self.conn.commit()
        cur.close()

    def getRatedAuthorsForUser(self, user_id, rating):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT a.name
            FROM user_books ub
            JOIN book_authors ba ON ub.work_id = ba.work_id
            JOIN authors a ON ba.author_id = a.author_id
            WHERE ub.user_id = %s AND ub.rating = %s;
        """, (user_id, rating))
        authors = [row[0] for row in cur.fetchall()]
        cur.close()
        return authors
    
    #TODO: Make query more efficient - one db call instead of one for each book
    def getRatedBooksForUser(self, user_id, rating):
        """return a list of book objects for the books the user has rated with the given rating"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.work_id, b.title, b.subtitle, b.description, b.isbn10, b.isbn13
            FROM user_books ub
            JOIN books b ON ub.work_id = b.work_id
            WHERE ub.user_id = %s AND ub.rating = %s;
        """, (user_id, rating))
        books = []
        for row in cur.fetchall():
            bookRepo = BooksRepository(self.conn)
            book = bookRepo.resultToBook(row)
            books.append(book)
        cur.close()
        return books
    
    def whichShelfIsBookOnForUser(self, user_id, work_id):
        """return the name of the shelf a book is on for a user (e.g. 'to-read', 'currently-reading', 'read')"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT shelf
            FROM user_books
            WHERE user_id = %s AND work_id = %s;
        """, (user_id, work_id))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None