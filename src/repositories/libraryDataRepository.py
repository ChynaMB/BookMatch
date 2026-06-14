from database.library import Library

class LibraryDataRepository:
    def __init__(self, library: Library):
        self.library = library

    def getNumOfBooks(self):
        """count the number of books in the library"""
        result = self.library.fetchone("""
            SELECT COUNT(*) as num_books
            FROM books
        """)
        return result[0] if result else None
    
    def getNumOfUsers(self):
        """count the number of users in the library"""
        result = self.library.fetchone("""
            SELECT COUNT(*) as num_users
            FROM users
        """)
        return result[0] if result else None
    
    def getNumOfAuthors(self):
        """count the number of authors in the library"""
        result = self.library.fetchone("""
            SELECT COUNT(*) as num_authors
            FROM authors
        """)
        return result[0] if result else None
    
    def getNumOfSubjects(self):
        """count the number of subjects in the library"""
        result = self.library.fetchone("""
            SELECT COUNT(*) as num_subjects
            FROM subjects
        """)
        return result[0] if result else None
    
    def getAverageBooksRating(self):
        result = self.library.fetchone("""
            SELECT average_books_rating
            FROM library_data
        """)
        return result[0] if result else None

    def getAverageBooksRatingCount(self):
        result = self.library.fetchone("""
            SELECT average_books_rating_count
            FROM library_data
        """)
        return result[0] if result else None