from src.repositories.authorsRepository import AuthorsRepository
from src.repositories.subjectsRepository import SubjectsRepository
from src.repositories.booksRepository import BooksRepository
from src.services.embedder import Embedder
import requests
import time

class BookImporter:
    def __init__(self, conn, isbns: list):
        self.conn = conn
        self.openLibraryURL = "https://openlibrary.org"
        self.booksRepo = BooksRepository(self.conn)
        self.subjectsRepo = SubjectsRepository(self.conn)
        self.embedder = Embedder(self.conn)
        self.isbns = isbns
        self.works = {}

    def getWorksFromISBNS(self):
        #check database for work_id, 
            ISBNnotInDatabase = []
            for isbn_tuple in self.isbns:
                isbn10, isbn13 = isbn_tuple
                if self.booksRepo.getWorkIDByISBN10(isbn10):
                    self.works[self.booksRepo.getWorkIDByISBN10(isbn10)] = (isbn10, isbn13)
                elif self.booksRepo.getWorkIDByISBN13(isbn13):
                    self.works[self.booksRepo.getWorkIDByISBN13(isbn13)] = (isbn10, isbn13)
                else:
                    ISBNnotInDatabase.append(isbn10 if isbn10 else isbn13)
                                             
            #batch fetch from API and add to database
            keys = ",".join([f"ISBN:{isbn}" for isbn in ISBNnotInDatabase])
            url = f"{self.openLibraryURL}/api/books?bibkeys={keys}&format=json&jscmd=data"
            response = requests.get(url)
            data = response.json()

            workIDS = set() #use a set to avoid duplicates
            for entry in data.values():
                if "works" in entry:
                    workID = entry["works"][0]["key"] #example:/works/OL45883W        
                    if workID not in workIDS:
                        workIDS.add(workID)
                        isbn10 = entry.get("identifiers", {}).get("isbn_10", [None])[0]
                        if isbn10 in ISBNnotInDatabase:
                            self.works[workID] = (isbn10, None)
                        elif isbn13 in ISBNnotInDatabase:
                            isbn13 = entry.get("identifiers", {}).get("isbn_13", [None])[0]
                            self.works[workID] = (None, isbn13)  
                        else:
                            print(f"Warning: Work {workID} not added to library because its ISBNs were not in the csv.")        
        
    def addBooksToLibrary(self):
        """Adds books to the library database by fetching book details from the Open Library API using ISBNs. 
        It first checks if the book already exists in the database to avoid duplicates, 
        then uses fetches details for new books and adds them to the database. 
        (book, authors, book_authors, subjects and book_subjects tables)"""
        for workID, (isbn10, isbn13) in self.works.items():
            if self.booksRepo.getBookByWorkID(workID):
                continue  #skip if book already exists

            url = f"{self.openLibraryURL}{workID}.json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error fetching details for work {workID}: {response.status_code}")
                continue

            data = response.json()
            title = data.get("title", "Unknown Title")
            subtitle = data.get("subtitle")
            description = data.get("description", {}).get("value") if isinstance(data.get("description"), dict) else data.get("description")
            subjects = data.get("subjects", [])
            authors = data.get("authors", [])

            book_id = self.booksRepo.insertBook(workID, title, subtitle, description, isbn10, isbn13)

            #add subjects to the database and link them to the book
            #TODO: make subject handling more robust (e.g. handle duplicates, edge cases, etc.)
            for subject in subjects:
                self.subjectsRepo.addSubjectToBook(book_id, subject)

            #rating not required as they are pulled from the csv and updated separately

            #create and add embedding and similarity scores for the new book
            self.embedder.bookEmbedder(workID, title, subtitle, description, subjects)
            
            for author in authors:
                author_key = author["author"]["key"]
                author_url = f"{self.openLibraryURL}{author_key}.json"
                author_response = requests.get(author_url)
                if author_response.status_code != 200:
                    print(f"Error fetching details for author {author_key}: {author_response.status_code}")
                    continue
                author_data = author_response.json()
                author_name = author_data.get("name", "Unknown Author")
                author_id = AuthorsRepository(self.conn).getOrCreateAuthor(author_name)

            time.sleep(1)  #sleep for a bit to avoid hitting API rate limits (1 second)   

    def importBooks(self):
        """Main method to import books into the library. It first retrieves work IDs for the given ISBNs, 
        then adds any new books to the library database."""
        self.getWorksFromISBNS()
        time.sleep(1)  #sleep for a bit to avoid hitting API rate limits (1 second)
        self.addBooksToLibrary()
