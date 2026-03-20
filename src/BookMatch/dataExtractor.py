import pandas as pd
import requests
import numpy as np
from userProfile import UserProfile
from book import Book
from itertools import combinations
import networkx as nx
from collections import Counter

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

    def fetchWorksFromISBNS(self, ISBNS: list) ->list[tuple[str, str]]:
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
                        ISBN_workIDS.append((isbn10, workID))
                    else:
                        isbn13 = entry.get("identifiers", {}).get("isbn_13", [None])[0]
                        ISBN_workIDS.append((isbn13, workID))
                    
        return ISBN_workIDS #return a list of tuples (isbn, workID)
    
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
        for isbn, workID in ISBN_workIDS:
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

                #add book data to database
                self.library.addBookData(workID, title, author, averageRating, subjects, description)

            bookInfo[(isbn, workID)] = (title, author, subjects, description, averageRating, ratingCount)

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
        for (isbn, workID) in bookInfo.keys():
            if self.library.isBookInLibrary(workID): #check if book is in library.db
                continue
            title, author, subjects, description, averageRating, ratingCount = bookInfo[(isbn, workID)]
            bookShelf.append(Book(workID, isbn, title, author, subjects, description, averageRating, ratingCount, self.library))
        return bookShelf
    
    def addBookToBookShelf(self, bookShelf, workID, isbn, title, author, subjects, description, averageRating, ratingCount):
        """Given a bookShelf, update the bookShelf with a new book if it is not already in the library"""
        if self.library.isBookInLibrary(workID):
            return bookShelf
        bookShelf.append(Book(workID, isbn, title, author, subjects, description, averageRating, ratingCount, self.library))
        return bookShelf
    
    #TODO: Correct the naming practices and logic of this method
    def createSubjectGraph(self, bookInfo: dict, weightMultiplier) -> nx.Graph:
        """
        Build a subject graph from a user's book subjects.
        - Nodes: subjects with 'frequency' attribute (capped)
        - Edges: co-occurrence of subjects in the same book (capped)
        - Ceiling calculated as mean + k * standard deviation
        """
        
        nodeFrequency = Counter()                    # Counter to track how many times each subject appears across all books
        edgeWeights = Counter()        # Counter to track co-occurrence counts for each pair of subjects

        # Step 1: collect frequencies and edge co-occurrences
        for (_, _), (_, _, subjects, _, _, _) in bookInfo.items():
            # Extract and clean subjects for this book:
            # strip whitespace, convert to lowercase, ignore empty strings
            cleaned = [subject.strip().lower() for subject in subjects if subject and subject.strip()]
            
            if len(cleaned) < 1:                 # Skip this book if no subjects remain after cleaning
                continue

            # Node frequency: increment count of each subject by 1 for this book
            for subject in cleaned:
                nodeFrequency[subject] += weightMultiplier

            # Edge weights: for each unique pair of subjects in this book, increment co-occurrence count
            for subject1, subject2 in combinations(cleaned, 2):
                edge = tuple(sorted((subject1, subject2)))   # Sort subjects to ensure edge is undirected (s1-s2 same as s2-s1)
                edgeWeights[edge] += weightMultiplier

        # Step 2: compute dynamic ceilings
        if nodeFrequency:
            frequency = np.array(list(nodeFrequency.values())) # Convert frequencies to numpy array for mean/std calculation
            meanFrequency = frequency.mean() # Calculate mean frequency of subjects
            frequencyStandardDeviation = frequency.std()# Calculate standard deviation of frequencies
            maxNodeFreq = meanFrequency + self.ceilingFactor * frequencyStandardDeviation  # node frequency ceiling
        else:
            maxNodeFreq = 0 #If there are no nodes, set ceiling to 0 to avoid adding any nodes

        if edgeWeights:
            edgeOccurences = np.array(list(edgeWeights.values())) # Convert edge co-occurrence counts to numpy array for mean/std calculation
            meanEdgeOccurence = edgeOccurences.mean() # Calculate mean co-occurrence count for edges
            edgeOccurenceStandardDeviation = edgeOccurences.std() # Calculate standard deviation of edge co-occurrence counts
            maxEdgeWeight = meanEdgeOccurence + self.ceilingFactor * edgeOccurenceStandardDeviation  # edge weight ceiling
        else:
            maxEdgeWeight = 0 # If there are no edges, set ceiling to 0 to avoid adding any edges

        # Step 3: build the graph with capped nodes and edges
        subjectGraph = nx.Graph()

        # Add nodes with capped frequencies
        for subject, freq in nodeFrequency.items():
            capped_freq = min(freq, maxNodeFreq)   # apply ceiling
            subjectGraph.add_node(subject, frequency=capped_freq)

        # Add edges with capped weights
        for (subject1, subject2), w in edgeWeights.items():
            if subject1 in subjectGraph.nodes and subject2 in subjectGraph.nodes:
                capped_w = min(w, maxEdgeWeight)  # apply ceiling
                subjectGraph.add_edge(subject1, subject2, weight=capped_w)

        return subjectGraph

    def addSubjectsToSubjectGraph(self, subjectGraph, subjects, weightMultiplier):
        """Update an existing subject graph with subjects from a new book"""

        # Clean subjects: remove whitespace, lowercase, remove duplicates
        cleaned = list({s.strip().lower() for s in subjects if s and s.strip()})

        # If no valid subjects remain, nothing to update
        if not cleaned:
            return subjectGraph

        # ---- Step 1: update nodes ----
        for subject in cleaned:
            if subjectGraph.has_node(subject):
                subjectGraph.nodes[subject]['frequency'] += weightMultiplier
            else:
                subjectGraph.add_node(subject, frequency=weightMultiplier)

        # ---- Step 2: update edges ----
        for subject1, subject2 in combinations(cleaned, 2):
            if subjectGraph.has_edge(subject1, subject2):
                subjectGraph[subject1][subject2]['weight'] += weightMultiplier
            else:
                subjectGraph.add_edge(subject1, subject2, weight=weightMultiplier)

        # ---- Step 3: recompute ceilings using updated graph ----
        nodeFrequencies = np.array([data['frequency'] for _, data in subjectGraph.nodes(data=True)])
        edgeWeights = np.array([data['weight'] for _, _, data in subjectGraph.edges(data=True)])

        maxNodeFreq = nodeFrequencies.mean() + self.ceilingFactor * nodeFrequencies.std() if len(nodeFrequencies) else 0
        maxEdgeWeight = edgeWeights.mean() + self.ceilingFactor * edgeWeights.std() if len(edgeWeights) else 0

        # ---- Step 4: apply caps ----
        for node, data in subjectGraph.nodes(data=True):
            data['frequency'] = min(data['frequency'], maxNodeFreq)

        for u, v, data in subjectGraph.edges(data=True):
            data['weight'] = min(data['weight'], maxEdgeWeight)

        return subjectGraph

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
        
        subjectGraph = self.createSubjectGraph(fiveStarBookInfo, self.fiveStarWeight)
        for bookInfo in FourStarBookInfo.values():
            _, _, subjects, _, _, _ = bookInfo
            subjectGraph = self.addSubjectsToSubjectGraph(subjectGraph, subjects, self.fourStarWeight)
        
        return UserProfile(self.userID, fiveStarBookshelf, fourStarBookshelf, likedAuthors, 
                           subjectGraph, self.fiveStarWeight, self.fourStarWeight, self.library)