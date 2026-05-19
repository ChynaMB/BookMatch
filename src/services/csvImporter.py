from database.library import Library
from database.libraryConnection import connectToLibrary
from database.repositories.usersRepository import UsersRepository
from database.repositories.booksRepository import BooksRepository
from database.repositories.authorsRepository import AuthorsRepository
from database.repositories.bookshelfRepository import BookshelfRepository
from database.library import Library
from services.bookImporter import BookImporter
import pandas as pd
import requests

class CSVimporter:
    def __init__(self, conn, path):
        self.conn = conn
        self.path = path
        self.user_id = None
        self.isbns = []
        self.mostRecentDate = None
  
    def getUserID(self): return self.user_id

    def importCSV(self):
        self.user_id = UsersRepository(self.conn).createUser()
        print(f"Created new user with ID: {self.user_id}")

        self.getISBNSAndMostRecentDate(self.path)
        print(f"Extracted {len(self.isbns)} ISBNs from CSV.")
        print(f"Most recent date in CSV: {self.mostRecentDate}")

        bookImporter = BookImporter(self.isbns)
        print("Fetching work IDs for ISBNs and adding new books to the library...")
        bookImporter.importBooks()
        print("Finished importing books from CSV.")

        self.loadCSV()
        print("Finished loading CSV data into the library database.")

    #TODO: accomodate for missing data
    #TODO: make more effcient

    def getISBNSAndMostRecentDate(self, df):
        df = pd.read_csv(self.path)

        isbns = []
        most_recent_date = None

        for _, row in df.iterrows():
            isbn10 = row.get("ISBN")
            isbn13 = row.get("ISBN13")
            isbns.append((isbn10,isbn13))

            date_added = row.get("Date Added")
            if pd.notna(date_added): #skips garbage values
                if most_recent_date is None or date_added > most_recent_date:
                    most_recent_date = date_added

        self.isbns = isbns
        self.mostRecentDate = most_recent_date

    def loadCSV(self):
        booksRepo = BooksRepository(self.conn)
        authorsRepo = AuthorsRepository(self.conn)
        bookshelfRepo = BookshelfRepository(self.conn)

        df = pd.read_csv(self.path)

        for _, row in df.iterrows():
            title = row["Title"]
            author = row.get("Author")
            additional_authors = str(row.get("Additional Authors")).split(",")
            isbn10 = row.get("ISBN")
            isbn13 = row.get("ISBN13")
            rating = row.get("My Rating")
            average_rating = row.get("Average Rating") 
            date_added = row.get("Date Added")
            review = row.get("My Review")
            read_count = row.get("Read Count")
            shelf = row.get("Exclusive Shelf")

            #get work_id from isbn
            work_id = booksRepo.getWorkIDByISBN10(isbn10) if isbn10 else None
            if not work_id and isbn13:
                work_id = booksRepo.getWorkIDByISBN13(isbn13)
            if not work_id:
                print(f"Warning: Book '{title}' not added to library because its ISBNs were not in the database.")
                continue
            
            #book details - work_id, title, isbn, isbn13
            booksRepo.insertBook(work_id, title, isbn=isbn10, isbn13=isbn13) #insert book with basic details to ensure it exists in the database
            if title:
                booksRepo.updateBookTitle(work_id, title)  #update title in case it was missing or different in the database

            #book details - average rating
            if average_rating and self.mostRecentDate:
                booksRepo.updateBookRating(work_id, average_rating, self.mostRecentDate)

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
    
