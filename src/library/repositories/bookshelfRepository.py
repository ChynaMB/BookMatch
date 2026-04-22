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

    def getUserBookshelf(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM user_books WHERE user_id = %s;
        """, (user_id,))
        result = cur.fetchall()
        cur.close()
        return result