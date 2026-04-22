class AuthorsRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_or_create(self, name):
        cur = self.conn.cursor()

        cur.execute("SELECT author_id FROM authors WHERE name = %s;", (name,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            return existing[0]

        cur.execute("""
            INSERT INTO authors (name)
            VALUES (%s)
            RETURNING author_id;
        """, (name,))

        author_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return author_id