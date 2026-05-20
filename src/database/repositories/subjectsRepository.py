class SubjectsRepository:
    def __init__(self, conn):
        self.conn = conn

    def addSubject(self, subject_name):
        """add a subject to the database if it doesn't already exist"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO subjects (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING subject_id;
        """, (subject_name,))
        subject_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return subject_id

    def addSubjectToBook(self, work_id, subject_name):
        """add a subject to a book in the database if the relationship doesn't already exist"""
        #first ensure the subject exists in the subjects table and get its id
        subject_id = self.addSubject(subject_name)
        
        #then add the relationship to the book_subjects table
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO book_subjects (work_id, subject_id)
            VALUES (%s, %s)
            ON CONFLICT (work_id, subject_id) DO NOTHING;
        """, (work_id, subject_id))

        self.conn.commit()
        cur.close()