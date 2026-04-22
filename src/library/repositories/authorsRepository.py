class AuthorsRepository:
    def __init__(self, conn):
        self.conn = conn

    def getOrCreateAuthor(self, author_name):
        cur = self.conn.cursor()

        cur.execute("SELECT author_id FROM authors WHERE name = %s;", (author_name,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            return existing[0]

        cur.execute("""
            INSERT INTO authors (name)
            VALUES (%s)
            RETURNING author_id;
        """, (author_name,))

        author_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return author_id
    
    def upsertAuthorIntoBookAuthors(self, work_id, author_id):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO book_authors (work_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (work_id, author_id))
        self.conn.commit()
        cur.close()