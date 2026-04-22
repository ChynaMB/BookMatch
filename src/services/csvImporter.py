from library.libraryConnection import connectToLibrary
from library.repositories.booksRepository import BooksRepository
from library.repositories.authorsRepository import AuthorsRepository
from library.repositories.bookshelfRepository import BookshelfRepository
import pandas as pd

class CSVimporter:
    def __init__(self, path):
        self.conn = connectToLibrary()
        self.path = path
        self.user_id = 1 #database should generate user id

    #TODO: accomodate for missing data
    #TODO: make more effcient

    def import_csv(self):
        booksRepo = BooksRepository(self.conn)
        authorsRepo = AuthorsRepository(self.conn)
        bookshelfRepo = BookshelfRepository(self.conn)

        df = pd.read_csv(self.path)

        #get most recent date
        most_recent_date = None
        for _, row in df.iterrows():
            date_added = row.get("Date Added")
            if pd.notna(date_added): #skips garbage values
                if most_recent_date is None or date_added > most_recent_date:
                    most_recent_date = date_added

        for _, row in df.iterrows():
            work_id = str(row["Book Id"])
            title = row["Title"]
            author = row.get("Author")
            additional_authors = str(row.get("Additional Authors")).split(",")
            isbn = row.get("ISBN")
            isbn13 = row.get("ISBN13")
            rating = row.get("My Rating")
            average_rating = row.get("Average Rating") 
            date_added = row.get("Date Added")
            review = row.get("My Review")
            read_count = row.get("Read Count")
            shelf = row.get("Exclusive Shelf")

            #book details - word, title, isbn, isbn13
            booksRepo.insertBook(work_id, title, isbn=isbn, isbn13=isbn13)

            #book details - average rating
            booksRepo.updateBookRating(work_id, average_rating, most_recent_date)

            #authors - author and additional authors
            author_id = authorsRepo.getOrCreateAuthor(author)
            authorsRepo.upsertAuthorIntoBookAuthors(work_id,author_id)
            for author_name in additional_authors:
                author_name = author_name.strip()
                if author_name:
                    author_id = authorsRepo.getOrCreateAuthor(author_name)
                    authorsRepo.upsertAuthorIntoBookAuthors(work_id,author_id)

            #user data - users rating and review of the book
            bookshelfRepo.upsertBookIntoUserBookshelf(
                self.user_id,
                work_id,
                rating = rating,
                date_added = date_added,
                review = review,
                read_count = read_count, 
                shelf = shelf
            )

        self.conn.close()
        print("Import complete")