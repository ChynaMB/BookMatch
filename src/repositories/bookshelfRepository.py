from database.library import Library
from src.repositories.booksRepository import BooksRepository

class BookshelfRepository:
    def __init__(self, library: Library):
        self.library = library

    def upsertBookIntoUserBookshelf(self, user_id, work_id, rating=None, date_added=None, review=None, read_count=None, shelf=None):
        self.library.execute("""
            INSERT INTO user_bookshelf (user_id, work_id, rating, date_added, review, read_count, shelf)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, work_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                date_added = EXCLUDED.date_added,
                review = EXCLUDED.review,
                read_count = EXCLUDED.read_count,
                shelf = EXCLUDED.shelf;
        """, (user_id, work_id, rating, date_added, review, read_count, shelf))

    def getRatedAuthorsForUser(self, user_id, rating):
        result = self.library.fetchall("""
            SELECT a.name
            FROM user_bookshelf ub
            JOIN book_authors ba ON ub.work_id = ba.work_id
            JOIN authors a ON ba.author_id = a.author_id
            WHERE ub.user_id = %s AND ub.rating = %s;
        """, (user_id, rating))
        authors = [row[0] for row in result]
        return authors
    
    #TODO: Make query more efficient - one db call instead of one for each book
    def getRatedBooksForUser(self, user_id, rating):
        """return a list of book objects for the books the user has rated with the given rating"""
        result = self.library.fetchall("""
            SELECT b.work_id, b.title, b.subtitle, b.description, b.isbn10, b.isbn13,
                   b.average_rating, b.rating_update_date, b.rating_count
            FROM user_bookshelf ub
            JOIN books b ON ub.work_id = b.work_id
            WHERE ub.user_id = %s AND ub.rating = %s;
        """, (user_id, rating))
        books = []
        book_repo = BooksRepository(self.library)
        for row in result:
            books.append(book_repo.resultToBook(row))
        return books
    
    def whichShelfIsBookOnForUser(self, user_id, work_id):
        """return the name of the shelf a book is on for a user (e.g. 'to-read', 'currently-reading', 'read')"""
        result = self.library.fetchone("""
            SELECT shelf
            FROM user_bookshelf
            WHERE user_id = %s AND work_id = %s;
        """, (user_id, work_id))
        return result[0] if result else None
