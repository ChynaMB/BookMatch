import pandas as pd
import requests
from userProfile import UserProfile
from book import Book


class DataExtractor:
    def __init__(self, csv_path: str, library):
        self.csv_path = csv_path
        self.csvDataFrame = pd.read_csv(csv_path)

        self.library = library
        self.userID = self.library.addUser()

        self.openLibraryURL = "https://openlibrary.org"
        self.googleBooksURL = "https://www.googleapis.com/books/v1/volumes"
        self.hardcoverURL = "https://api.hardcover.io/v1/books"

        self.fiveStarWeight = 1
        self.fourStarWeight = 0.7
        self.ceilingFactor = 1.5 #number of standard deviations above the mean to set as the ceiling for node frequencies and edge weights in the subject graph

    def fetchWorksFromISBNS(self, ISBNS: list) ->list[tuple[str, str, str]]:
        """Given a list of ISBNs, return a list of works (work ID)
        we use wworks instead of isbn because some books have multiple editions with different ISBNs, 
        but they all belong to the same work"""
        keys = ",".join([f"ISBN:{isbn}" for isbn in ISBNS])
        url = f"{self.openLibraryURL}/api/books?bibkeys={keys}&format=json&jscmd=data"
        response = requests.get(url)
        data = response.json()

        workIDS = set() #use a set to avoid duplicates
        ISBN_workIDS = []
        for entry in data.values():
            if "works" in entry:
                workID = entry["works"][0]["key"] #example:/works/OL45883W        
                if workID not in workIDS:
                    workIDS.add(workID)
                    isbn10 = entry.get("identifiers", {}).get("isbn_10", [None])[0]
                    if isbn10 in ISBNS:
                        ISBN_workIDS.append((isbn10, None, workID))
                    else:
                        isbn13 = entry.get("identifiers", {}).get("isbn_13", [None])[0]
                        ISBN_workIDS.append((None, isbn13, workID))
                    
        return ISBN_workIDS #return a list of tuples (isbn, isbn13, workID)
    
    def getBookInfo(self, ISBNS) -> dict:
        """
        Given a list of ISBNs, first get WorkIDs
        fetch all data from library.db bookData using workID first, then use API calls if not in database

        using open library API and workIDs, get book title, author and subject

        using google books API and isbns, fetch book description 

        using ISBNS, fetch average ratings and rating count from open library API, google books API, 
        and hardcover API for each book. Use the average of the ratings from the three sources as the final 
        rating for the book. If a source does not have a rating for the book, ignore that 
        source in the average calculation.
        
        return a dictionary with key (isbn, workID) and value (title, author, subjects, description, averageRating, ratingCount)
        """
        if ISBNS is None or len(ISBNS) == 0:
            raise ValueError("ISBNS list cannot be empty")

        bookInfo = {} #key: (isbn, work), value: (title, author, subjects, description, averageRating, ratingCount) 
        #Get workIDs from ISBNs 
        ISBN_workIDS = self.fetchWorksFromISBNS(ISBNS)
        #Check database for book data using workIDs, if not in database, fetch from APIs and add to database
        for isbn, isbn13, workID in ISBN_workIDS:
            if self.library.isBookInLibrary(workID):
                title = self.library.getTitleFromBookData(workID)
                author = self.library.getAuthorFromBookData(workID)
                subjects = self.library.getSubjectsFromBookData(workID)
                description = self.library.getDescriptionFromBookData(workID)
                averageRating = self.library.getAverageRatingFromBookData(workID)
                ratingCount = self.library.getRatingCountFromBookData(workID)
            else:
                title, author, subjects = self.fetchBookDataFromOpenLibrary(workID)
                description = self.fetchBookDescriptionFromGoogleBooks(isbn)
                averageRating, ratingCount = self.fetchRatingsFromAPIs(isbn)
                
                #create a book object to add the book data to the database and create the book vector embedding
                book = Book(workID, isbn, isbn13, title, author, subjects, description, averageRating, ratingCount, self.library) 
               
            bookInfo[(isbn, isbn13, workID)] = (title, author, subjects, description, averageRating, ratingCount)

        return bookInfo

    def fetchBookDataFromOpenLibrary(self, workID):
        """Given a workID, fetch the book title, author and subjects from the open library API"""
        url = f"{self.openLibraryURL}{workID}.json"
        response = requests.get(url)
        data = response.json()
        title = data.get("title", "Unknown Title")
        author = data.get("authors", [{"name": "Unknown Author"}])[0]["name"]
        subjects = data.get("subjects", [])
        return title, author, subjects
    
    def fetchBookDescriptionFromGoogleBooks(self, isbn):
        """Given an ISBN, fetch the book description from the google books API"""
        url = f"{self.googleBooksURL}?q=isbn:{isbn}"
        response = requests.get(url)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["volumeInfo"].get("description", "No description available")
        else:
            return "No description available"
        
    def fetchRatingsFromAPIs(self, isbn):
        """Given an ISBN, fetch the average rating and rating count from the open library API, google books API, and hardcover API for each book. 
        Use the average of the ratings from the three sources as the final rating for the book. If a source does not have a rating for the book, ignore that source in the average calculation."""
        ratings = []
        ratingCounts = []
        #fetch from open library API
        url = f"{self.openLibraryURL}/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        response = requests.get(url)
        data = response.json()
        if f"ISBN:{isbn}" in data:
            ol_rating = data[f"ISBN:{isbn}"].get("average_rating")
            ol_rating_count = data[f"ISBN:{isbn}"].get("rating_count")
            if ol_rating is not None:
                ratings.append(ol_rating)
            if ol_rating_count is not None:
                ratingCounts.append(ol_rating_count)

        #fetch from google books API
        url = f"{self.googleBooksURL}?q=isbn:{isbn}"
        response = requests.get(url)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            gb_info = data["items"][0]["volumeInfo"]
            gb_rating = gb_info.get("averageRating")
            gb_rating_count = gb_info.get("ratingsCount")
            if gb_rating is not None:
                ratings.append(gb_rating)
            if gb_rating_count is not None:
                ratingCounts.append(gb_rating_count)

        #fetch from hardcover API (if we want to use it later)

        if ratings:
            averageRating = sum(ratings) / len(ratings)
        else:
            averageRating = None

        if ratingCounts:
            totalRatingCount = sum(ratingCounts)
        else:
            totalRatingCount = None

        return averageRating, totalRatingCount
#TODO: update liked authors methods to combine them into one
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

    def createBookShelf(self, bookInfo: dict) -> list:
        """Given a list of works, check library.db to see if we have a submition for each work
        if not, create a Book for it so it can be stored in the library"""
        bookShelf = []
        for (isbn, isbn13, workID) in bookInfo.keys():
            if self.library.isBookInLibrary(workID): #check if book is in library.db
                continue
            title, author, subjects, description, averageRating, ratingCount = bookInfo[(isbn, isbn13, workID)]
            bookShelf.append(Book(workID, isbn, isbn13, title, author, subjects, description, averageRating, ratingCount, self.library))
        return bookShelf
    
    def addBookToBookShelf(self, bookShelf, workID, isbn, isbn13, title, author, subjects, description, averageRating, ratingCount):
        """Given a bookShelf, update the bookShelf with a new book if it is not already in the library"""
        if self.library.isBookInLibrary(workID):
            return bookShelf
        bookShelf.append(Book(workID, isbn, isbn13, title, author, subjects, description, averageRating, ratingCount, self.library))
        return bookShelf

    def createUserProfile(self) -> UserProfile:
        """Create a user profile based on the subject graph"""
        fiveStarISBNS = self.csvDataFrame[self.csvDataFrame['My Rating'] == 5]
        fourStarISBNS = self.csvDataFrame[self.csvDataFrame['My Rating'] == 4]
        
        fiveStarBookInfo = self.getBookInfo(fiveStarISBNS['ISBN'].tolist())
        fiveStarBookshelf = self.createBookShelf(fiveStarBookInfo)

        FourStarBookInfo = self.getBookInfo(fourStarISBNS['ISBN'].tolist())
        fourStarBookshelf = self.createBookShelf(FourStarBookInfo)

        fiveStarAuthors = fiveStarISBNS['Author'].tolist()
        fourStarAuthors = fourStarISBNS['Author'].tolist()
        likedAuthors = self.getLikedAuthors(fiveStarAuthors, self.fiveStarWeight)
        for author in fourStarAuthors:
            likedAuthors = self.updateLikedAuthors(author, likedAuthors, self.fourStarWeight)
        
        
        return UserProfile(self.userID, fiveStarBookshelf, fourStarBookshelf, likedAuthors, self.fiveStarWeight, 
                           self.fourStarWeight, self.ceilingFactor, self.library)