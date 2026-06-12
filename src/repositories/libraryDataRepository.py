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
    
    def getNumOfBooks(self):
        """count the number of books in the library"""
        cur = self.conn.cursor()
        cur.execute(""""
            SELECT COUNT(*) as num_books
            FROM books
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    
    def getNumOfUsers(self):
        """count the number of users in the library"""
        cur = self.conn.cursor()
        cur.execute(""""
            SELECT COUNT(*) as num_users
            FROM users
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    
    def getNumOfAuthors(self):
        """count the number of authors in the library"""
        cur = self.conn.cursor()
        cur.execute(""""
            SELECT COUNT(*) as num_authors
            FROM authors
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    
    def getNumOfSubjects(self):
        """count the number of subjects in the library"""
        cur = self.conn.cursor()
        cur.execute(""""
            SELECT COUNT(*) as num_subjects
            FROM subjects
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    
    def getAverageBooksRating(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT average_books_rating
            FROM library_data
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None

    def getAverageBooksRatingCount(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT average_books_rating_count
            FROM library_data
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None