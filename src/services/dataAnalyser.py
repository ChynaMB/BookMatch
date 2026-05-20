import pandas as pd
import requests
from src.database.repositories.bookshelfRepository import BookshelfRepository
from src.database.repositories.embeddingRepository import EmbeddingRepository

"""
DataAnalyser class for analysing user data to create graphs and embeddings.
"""

class DataAnalyser:
    def __init__(self, conn, user_id, fiveStarWeight=1, fourStarWeight=0.7, ceilingFactor=1.5):
        self.userID = user_id
        self.bookshelfRepo = BookshelfRepository(conn)
        self.embeddingRepo = EmbeddingRepository(conn)
        
        self.fiveStarWeight = fiveStarWeight
        self.fourStarWeight = fourStarWeight
        self.ceilingFactor = ceilingFactor #number of standard deviations above the mean to set as the ceiling for node frequencies and edge weights in the subject graph

        self.fiveStarBooks = []
        self.fourStarBooks = []
        self.likedAuthors = {} #key: author name, value: weighted occurence based on author's books in five star and four star bookshelves

    def getLikedAuthors(self):
        """Return a dictionairy of liked authors based on the frequency of authors in the 4 and 5 star ratings"""
        fiveStarAuthors = self.bookshelfRepo.getRatedAuthorsForUser(self.fiveStarWeight, self.userID)
        fourStarAuthors = self.bookshelfRepo.getRatedAuthorsForUser(self.fourStarWeight, self.userID)

        authorFrequency = {}
        for author in fiveStarAuthors:
            if author in authorFrequency:      
                authorFrequency[author] +=  self.fiveStarWeight
            else:
                authorFrequency[author] = 1
        for author in fourStarAuthors:
            if author in authorFrequency:      
                authorFrequency[author] +=  self.fourStarWeight
            else:
                authorFrequency[author] = 1

        self.likedAuthors = authorFrequency

    def getRatedBooks(self):
        """get a list of workIDs for the books the user has rated 4 or 5 stars"""
        self.fiveStarBooks = self.bookshelfRepo.getRatedBooksForUser(self.userID,self.fiveStarWeight)
        self.fourStarBooks = self.bookshelfRepo.getRatedBooksForUser(self.userID,self.fourStarWeight)

    def analyseUserData(self):
        """analyse the user's data to create a user profile with a subject graph and vector embedding"""
        self.getLikedAuthors()
        self.getRatedBooks()
        #create book graph