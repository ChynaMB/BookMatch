class LibraryDataRepository:
    def __init__(self, conn):
        self.conn = conn

    def getAverageBooksRating(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT average_books_rating
            FROM library_data
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None