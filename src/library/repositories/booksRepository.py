class BooksRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert_book(self, work_id, title, subtitle=None, description=None, isbn=None, isbn13=None):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO books (work_id, title, subtitle, description, isbn, isbn13)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (work_id) DO NOTHING;
        """, (work_id, title, subtitle, description, isbn, isbn13))
        self.conn.commit()
        cur.close()

    def get_book(self, work_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books WHERE work_id = %s;", (work_id,))
        result = cur.fetchone()
        cur.close()
        return result

    def get_all_books(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM books;")
        result = cur.fetchall()
        cur.close()
        return result