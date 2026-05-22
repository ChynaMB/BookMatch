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

        data = cur.fetchone()
        author_id = data[0] if data else None
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
        
    def getBookAuthors(self, work_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT authors.name
            FROM authors
            JOIN book_authors
            ON authors.author_id = book_authors.author_id
            WHERE book_authors.work_id = %s;
        """, (work_id,))

        author_names = [row[0] for row in cur.fetchall()]
        cur.close()
        return author_names
            