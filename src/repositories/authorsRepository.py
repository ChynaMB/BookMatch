from database.library import Library

class AuthorsRepository:
    def __init__(self, library: Library):
        self.library = library

    def getOrCreateAuthor(self, author_name):
        existing = self.library.fetchone("SELECT author_id FROM authors WHERE name = %s;", (author_name,))
        
        if existing:
            return existing[0]

        author_id = self.library.fetchone("""
            INSERT INTO authors (name)
            VALUES (%s)
            RETURNING author_id;
        """, (author_name,))

        return author_id[0] if author_id else None
       
    def upsertAuthorIntoBookAuthors(self, work_id, author_id):
        self.library.execute("""
            INSERT INTO book_authors (work_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (work_id, author_id))
        
    def getBookAuthors(self, work_id):
        result = self.library.fetchall("""
            SELECT authors.name
            FROM authors
            JOIN book_authors
            ON authors.author_id = book_authors.author_id
            WHERE book_authors.work_id = %s;
        """, (work_id,))

        author_names = [row[0] for row in result]
        return author_names
            