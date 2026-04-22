class SubjectsRepository:
    def __init__(self, conn):
        self.conn = conn

    def getOrCreateSubject(self, name):
        cur = self.conn.cursor()

        cur.execute("SELECT subject_id FROM subjects WHERE name = %s;", (name,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            return existing[0]

        cur.execute("""
            INSERT INTO subjects (name)
            VALUES (%s)
            RETURNING subject_id;
        """, (name,))

        subject_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return subject_id