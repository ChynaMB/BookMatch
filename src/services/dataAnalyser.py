import pandas as pd
import networkx as nx
from itertools import combinations
import numpy as np
import requests
from database.repositories.booksRepository import BooksRepository
from src.database.repositories.bookshelfRepository import BookshelfRepository
from src.database.repositories.embeddingRepository import EmbeddingRepository
from src.database.repositories.graphRepository import GraphRepository

"""
DataAnalyser class for analysing user data 
to create subject graphs and userembeddings
and to identify liked authors based on the user's ratings.
"""

class DataAnalyser:
    def __init__(self, conn, user_id, fiveStarWeight=1, fourStarWeight=0.7, ceilingFactor=1.5):
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
        self.fiveStarBookshelf = self.bookshelfRepo.getRatedBooksForUser(self.userID,self.fiveStarWeight)
        self.fourStarBookshelf = self.bookshelfRepo.getRatedBooksForUser(self.userID,self.fourStarWeight)

    #TODO: Clean up and optimise this method - especially the if-else statements in the loops
    def createUserEmbedding(self):
        """Uses the users five and four star books to create a vector embedding
        representing the user's reading preferences. This is done by averaging the vector embeddings 
        of the books in the five and four star bookshelves, with more weight given to the five star books."""
        userProfileVectorEmbedding = []
        for book in self.fiveStarBookshelf:
            bookVector = self.embeddingRepo.getEmbedding('book', book.getWorkID())
            for i, vectorEntry in enumerate(bookVector):
                if len(userProfileVectorEmbedding) == 0:
                    userProfileVectorEmbedding.append(vectorEntry * self.fiveStarWeight)
                else:
                    userProfileVectorEmbedding[i] += vectorEntry * self.fiveStarWeight

        for book in self.fourStarBookshelf:
            bookVector = self.embeddingRepo.getEmbedding('book', book.getWorkID())
            for i, vectorEntry in enumerate(bookVector):
                if len(userProfileVectorEmbedding) == 0:
                    userProfileVectorEmbedding.append(vectorEntry * self.fourStarWeight)
                else:
                    userProfileVectorEmbedding[i] += vectorEntry * self.fourStarWeight
        
        totalWeight = len(self.fiveStarBookshelf) * self.fiveStarWeight + len(self.fourStarBookshelf) * self.fourStarWeight
        if totalWeight == 0:
            return None
        
        for i in range(len(userProfileVectorEmbedding)):
            userProfileVectorEmbedding[i] = userProfileVectorEmbedding[i] / totalWeight

        self.embeddingRepo.addUserEmbedding(self.userID, userProfileVectorEmbedding)

    #TODO: Clean up and optimise this method - especially the if-else statements in the loops
    #TODO: Also consider edge cases (e.g. no books, all books have the same subjects, etc.) and how to handle them.
    def createSubjectGraph(self):
        """
        Build a subject graph from a user's book subjects.
        - Nodes: subjects with 'frequency' attribute (capped)
        - Edges: co-occurrence of subjects in the same book (capped)
        - Ceiling calculated as mean + k * standard deviation
        """
        
        nodeFrequency = {}    
        edgeWeights = {}

        # Step 1: collect frequencies and edge co-occurrences
        for book in self.fiveStarBookshelf:
            subjects = book.getSubjects()
            for subject in subjects:
                nodeFrequency[subject] = nodeFrequency.get(subject, 0) + self.fiveStarWeight 

            # Edge weights: for each unique pair of subjects in this book, increment co-occurrence count
            for subject1, subject2 in combinations(set(subjects), 2):
                edgeWeights[(subject1, subject2)] = edgeWeights.get((subject1, subject2), 0) + self.fiveStarWeight

        for book in self.fourStarBookshelf:
            subjects = book.getSubjects()
            for subject in subjects:
                nodeFrequency[subject] = nodeFrequency.get(subject, 0) + self.fourStarWeight

            for subject1, subject2 in combinations(set(subjects), 2):
                edgeWeights[(subject1, subject2)] = edgeWeights.get((subject1, subject2), 0) + self.fourStarWeight

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

        self.subjectGraph = subjectGraph
        self.graphRepo.addSubjectGraph(self.userID, subjectGraph)

    def analyseUserData(self):
        """analyse the user's data to create a user profile with a subject graph and vector embedding"""
        self.getLikedAuthors()
        self.getRatedBooks()
        self.createUserEmbedding()
        self.createSubjectGraph()
