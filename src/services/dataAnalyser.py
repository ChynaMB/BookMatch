from collections import Counter
import networkx as nx
from itertools import combinations
import numpy as np
from database.repositories.booksRepository import BooksRepository
from src.database.repositories.bookshelfRepository import BookshelfRepository
from src.database.repositories.embeddingRepository import EmbeddingRepository
from src.database.repositories.graphRepository import GraphRepository
from src.services.embedder import Embedder

"""
DataAnalyser class for analysing user data 
to create subject graphs and userembeddings
and to identify liked authors based on the user's ratings.
"""

class DataAnalyser:
    def __init__(self, conn, user_id, fiveStarWeight, fourStarWeight, ceilingFactor):
        self.userID = user_id
        self.bookshelfRepo = BookshelfRepository(conn)
        self.embeddingRepo = EmbeddingRepository(conn)
        self.graphRepo = GraphRepository(conn)
        
        self.fiveStarWeight = fiveStarWeight
        self.fourStarWeight = fourStarWeight
        self.ceilingFactor = ceilingFactor #number of standard deviations above the mean to set as the ceiling for node frequencies and edge weights in the subject graph

        self.fiveStarBookshelf = []
        self.fourStarBookshelf = []
        self.likedAuthors = {} #key: author name, value: weighted occurence based on author's books in five star and four star bookshelves
        self.subjectGraph = None #type: nx.Graph

    def findLikedAuthors(self):
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

    def findRatedBooks(self):
        """get a list of workIDs for the books the user has rated 4 or 5 stars"""
        self.fiveStarBookshelf = self.bookshelfRepo.getRatedBooksForUser(self.userID,5)
        self.fourStarBookshelf = self.bookshelfRepo.getRatedBooksForUser(self.userID,4)

    #TODO: Clean up and optimise this method - especially the if-else statements in the loops
    #TODO: Also consider edge cases (e.g. no books, all books have the same subjects, etc.) and how to handle them.
    def createSubjectGraph(self):
        """
        Build a subject graph from a user's book subjects.
        Nodes:  subjects with a 'frequency' attribute (capped)
        Edges:  subject co-occurrence within the same book (capped)
        Ceiling: mean + ceilingFactor * standard deviation
        """
        nodeFrequency: Counter = Counter()
        edgeWeights:   Counter = Counter()
    
        # --- Step 1: collect frequencies and co-occurrences ---
        bookshelves = [
            (self.fiveStarBookshelf, self.fiveStarWeight),
            (self.fourStarBookshelf, self.fourStarWeight),
        ]
    
        for shelf, weight in bookshelves:
            for book in shelf:
                subjects = book.getSubjects()
    
                if not subjects:
                    continue  # skip books with no subject data
    
                unique_subjects = set(subjects)
    
                for subject in unique_subjects:
                    nodeFrequency[subject] += weight
    
                for subject1, subject2 in combinations(unique_subjects, 2):
                    edgeWeights[(subject1, subject2)] += weight
    
        # --- Step 2: compute dynamic ceilings ---
        maxNodeFreq  = self.computeCeiling(list(nodeFrequency.values())) if nodeFrequency else 0
        maxEdgeWeight = self.computeCeiling(list(edgeWeights.values())) if edgeWeights else 0
    
        # --- Step 3: build the graph with capped values ---
        subjectGraph = nx.Graph()
    
        for subject, freq in nodeFrequency.items():
            subjectGraph.add_node(subject, frequency=min(freq, maxNodeFreq))
    
        for (subject1, subject2), weight in edgeWeights.items():
            # Both nodes are guaranteed to exist, but guard defensively
            if subject1 in subjectGraph and subject2 in subjectGraph:
                subjectGraph.add_edge(subject1, subject2, weight=min(weight, maxEdgeWeight))
    
        # --- Step 4: save graph ---
        self.subjectGraph = subjectGraph
        self.graphRepo.addSubjectGraph(self.userID, subjectGraph)
 
    def computeCeiling(self, values: list) -> float:
        """Return mean + k * std for a list of numeric values."""
        arr = np.array(values)
        return arr.mean() + self.ceilingFactor * arr.std()

    def analyseUserData(self):
        """analyse the user's data to create a user profile with a subject graph and vector embedding"""

        print("analysing user data...")
        self.findLikedAuthors()
        print("liked authors have been identified")

        self.findRatedBooks()
        print("rated books have been identified")

        embedder = Embedder(
            self.userID,
            self.fiveStarWeight, 
            self.fourStarWeight, 
            self.fiveStarBookshelf,
            self.fourStarBookshelf
        )
        embedder.createUserEmbedding()
        print("user embedding has been created and stored in the database")

        self.createSubjectGraph()
        print("subject graph has been created")
        print("finished analysing user data")
