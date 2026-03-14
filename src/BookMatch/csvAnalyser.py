import pandas as pd
from itertools import combinations
import requests
import networkx as nx
from library import Library
from userProfile import UserProfile
from book import Book

class CSVAnalyser:
    def __init__(self, csv_path: str, library):
        self.csv_path = csv_path
        self.csvDataFrame = pd.read_csv(csv_path)

        self.library = library
        self.userID = self.library.addUser()

        self.openLibraryURL = "https://openlibrary.org"
        self.failed_ISBNS = []
        
        self.fiveStarWeight = 2
        self.fourStarWeight = 1

    def getWorksFromISBNS(self, ISBNS: list) ->list[tuple[str, str]]:
        """Given a list of ISBNs, return a list of works (work ID)
        we use wworks instead of isbn because some books have multiple editions with different ISBNs, 
        but they all belong to the same work"""
        workIDS = set() #use a set to avoid duplicates
        failed_isbns = [] #keep track of failed ISBNs for debugging

        print(f"Getting works for ISBNs")
        for isbn in ISBNS:
            url = f"{self.openLibraryURL}/isbn/{isbn}.json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for ISBN {isbn}: {response.status_code}")
                self.failed_ISBNS.append(isbn)
                continue
            
            data = response.json()
            
            if "works" in data:
                workID = data["works"][0]["key"] #example:/works/OL45883W
                workIDS.add((isbn,workID))
            else:
                print(f"No work found for ISBN {isbn}")
                self.failed_ISBNS.append(isbn)

        return list(workIDS)
    
    def getBookInfo(self, workIDS: list[tuple[str, str]]) -> dict[tuple[str, str], tuple[list[str], str, str]]:
        """Given a list of works, return a dictionary of workID to subjects
        fetch from library.db bookData first, then API call if not in database
        also return book info: title and author(s)"""
        book_info = {} #key: (isbn, work), value: (title, author, subjects) 

        print(f"Getting subjects for works")
        for isbn, work in workIDS:
            # First, try to fetch from the database
            subjects = self.library.getSubjectsFromBookData(work)
            title = self.library.getTitleFromBookData(work)
            author = self.library.getAuthorFromBookData(work)
            if subjects is not None:
                book_info[(isbn, work)] = (subjects, title, author)
                continue

            #not in database, fetch from API
            url = f"{self.openLibraryURL}{work}.json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for work {work}: {response.status_code}")
                self.failed_ISBNS.append(isbn)
                continue
            
            data = response.json()

            if "subjects" in data:
                subjects = data["subjects"]
            else:
                print(f"No subjects found for work {work}")
                subjects = None

            if "title" in data:
                title = data["title"]
            else:
                print(f"No title found for work {work}")
                title = None

            if "authors" in data and len(data["authors"]) > 0:
                author = data["authors"][0]["name"]
            else:
                print(f"No author found for work {work}")
                author = None
            
            book_info[(isbn, work)] = (subjects, title, author)
            
        return book_info

    def getLikedAuthors(self, authors, weighting):
        """Return a dictionairy of liked authors based on the frequency of authors in the 4 and 5 star ratings"""
        authorFrequency = {}
        for author in authors:
            if author in authorFrequency:      
                authorFrequency[author] +=  weighting
            else:
                authorFrequency[author] = 1

        #return a new dictionary with only authors that have a frequency greater than 1
        return {author: freq for author, freq in authorFrequency.items() if freq > 1}

    def updateLikedAuthors(self, author, likedAuthors, weighting):
        if author in likedAuthors:
            likedAuthors[author] += weighting
        else:
            likedAuthors[author] = weighting
        return likedAuthors

    def createBookShelf(self, book_info: dict) -> list:
        """Given a list of works, check library.db to see if we have a submition for each work
        if not, create a Book for it so it can be stored in the library"""
        bookShelf = []
        for (isbn, workID) in book_info.keys():
            if self.library.isBookInLibrary(workID): #check if book is in library.db
                continue
            title, author, subjects = book_info[(isbn, workID)]
            bookShelf.append(Book(workID, isbn, title, author, subjects, self.library))
        return bookShelf
    
    def updateBookShelf(self, bookShelf, workID, isbn, subjects, title, author):
        """Given a bookShelf, update the bookShelf with a new book if it is not already in the library"""
        if self.library.isBookInLibrary(workID):
            return bookShelf
        bookShelf.append(Book(workID, isbn, title, author, subjects, self.library))
        return bookShelf
    
    #TODO: optimise this function
    def createUserProfile(self) -> UserProfile:
        """Create a user profile based on the subject graph"""
        fiveStarISBNS = self.csvDataFrame[self.csvDataFrame['My Rating'] == 5]
        fourStarISBNS = self.csvDataFrame[self.csvDataFrame['My Rating'] == 4]

        fiveStarWorks = self.getWorksFromISBNS(fiveStarISBNS['ISBN'].tolist())
        fiveStarBookInfo = self.getBookInfo(fiveStarWorks)

        fiveStarAuthors = fiveStarISBNS['Author'].tolist()
        likedAuthors = self.getLikedAuthors(fiveStarAuthors, self.fiveStarWeight)
        fiveStarBookshelf = self.createBookShelf(fiveStarBookInfo)

        fourStarWorks = self.getWorksFromISBNS(fourStarISBNS['ISBN'].tolist())
        fourStarBookInfo = self.getBookInfo(fourStarWorks)
        fourStarAuthors = fourStarISBNS['Author'].tolist()
        for author in fourStarAuthors:
            likedAuthors = self.updateLikedAuthors(author, likedAuthors, self.fourStarWeight)
        fourStarBookshelf = self.createBookShelf(fourStarBookInfo)
        
        return UserProfile(self.userID, fiveStarBookshelf, fourStarBookshelf, fiveStarWorks, fourStarWorks, likedAuthors, self.library)