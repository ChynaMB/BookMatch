class BooksRepository:
    def __init__(self, conn):
        self.conn = conn

    def insertBook(self, work_id, title, subtitle=None, description=None, isbn=None, isbn13=None):
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

    def getBook(self, work_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books WHERE work_id = %s;", (work_id,))
        result = cur.fetchone()
        cur.close()
        return result

    def getAllBooks(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books;")
        result = cur.fetchall()
        cur.close()
        return result
    
    