class BooksRepository:
    def __init__(self, conn):
        self.conn = conn
        self.bookEntries = ["work_id", "title", "subtitle", "description", "isbn", "isbn13"]

    def insertBook(self, work_id, title, subtitle=None, description=None, isbn=None, isbn13=None):
        """add a book to the libary only if it's work_id does not already exist (to avoid dublicates)"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO books (work_id, title, subtitle, description, isbn, isbn13)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (work_id) DO NOTHING;
        """, (work_id, title, subtitle, description, isbn, isbn13))
        self.conn.commit()
        cur.close()

    def updateBookRating(self, work_id, average_rating, rating_update_date):
        """If we have an average book rating from a more recent date, update the rating"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE books
            SET average_rating = ?, 
                rating_update_date = ?, 
            WHERE work_id = ?
            AND (
                rating_update_date IS NULL 
                OR rating_update_date < ?
            )
        """, (average_rating, rating_update_date, work_id, rating_update_date))
        self.conn.commit()
        cur.close()

    def updateBookTitle(self, work_id, title):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE books
            SET title = %s
            WHERE work_id = %s;
        """, (title, work_id))
        self.conn.commit()
        cur.close()

    def getBookByWorkID(self, work_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books WHERE work_id = %s;", (work_id,))
        result = cur.fetchone()
        cur.close()
        return result

    # TODO: Combine getBookByISBN10 and getBookByISBN13 into a single function that checks both fields, since some books may have one but not the other.
    def getBookByISBN10(self, isbn10):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books WHERE isbn10 = %s;", (isbn10,))
        result = cur.fetchone()
        cur.close()
        return result
    
    def getBookByISBN13(self, isbn13):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books WHERE isbn13 = %s;", (isbn13,))
        result = cur.fetchone()
        cur.close()
        return result

    #TODO combine getWorkIDByISBN10 and getWorkIDByISBN13 into a single function that checks both fields, since some books may have one but not the other.
    def getWorkIDByISBN10(self, isbn10):
        cur = self.conn.cursor()
        cur.execute("SELECT work_id FROM books WHERE isbn10 = %s;", (isbn10,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    
    def getWorkIDByISBN13(self, isbn13):
        cur = self.conn.cursor()
        cur.execute("SELECT work_id FROM books WHERE isbn13 = %s;", (isbn13,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None

    def getAllBooks(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books;")
        result = cur.fetchall()
        cur.close()
        return result
    