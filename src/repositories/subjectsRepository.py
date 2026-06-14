from database.library import Library

class SubjectsRepository:
    def __init__(self, library: Library):
        self.library = library

    def addSubject(self, subject_name):
        """add a subject to the database if it doesn't already exist"""
        result = self.library.fetchone("""
            INSERT INTO subjects (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING subject_id;
        """, (subject_name,))
        return result[0] if result else None

    def addSubjectToBook(self, work_id, subject_name):
        """add a subject to a book in the database if the relationship doesn't already exist"""
        #first ensure the subject exists in the subjects table and get its id
        subject_id = self.addSubject(subject_name)
        
        #then add the relationship to the book_subjects table
        self.library.execute("""
            INSERT INTO book_subjects (work_id, subject_id)
            VALUES (%s, %s)
            ON CONFLICT (work_id, subject_id) DO NOTHING;
        """, (work_id, subject_id))

    def getBookSubjects(self, workID):
        result = self.library.fetchall("""
            SELECT subjects.name
            FROM subjects 
            JOIN book_subjects
            ON subjects.subject_id = book_subjects.subject_id
            WHERE book_subjects.work_id = %s;
        """,(workID,))
        return [result[0] for result in result] if result else []