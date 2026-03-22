from collections import Counter
from itertools import combinations
import networkx as nx
import numpy as np

class SubjectGraph:
    def __init__(self, fiveStarBooks, fourStarBooks, fiveStarWeight: float, fourStarWeight: float, ceilingFactor: float):
        self.fiveStarBooks = fiveStarBooks
        self.fourStarBooks = fourStarBooks
        self.fiveStarWeight = fiveStarWeight
        self.fourStarWeight = fourStarWeight
        self.ceilingFactor = ceilingFactor

    #TODO: Correct the naming practices and logic of this method 
    #TODO: maybe break it up into smaller methods for clarity and maintainability. Also, consider edge cases (e.g. no books, all books have the same subjects, etc.) and how to handle them.
    def createSubjectGraph(self) -> nx.Graph:
        """
        Build a subject graph from a user's book subjects.
        - Nodes: subjects with 'frequency' attribute (capped)
        - Edges: co-occurrence of subjects in the same book (capped)
        - Ceiling calculated as mean + k * standard deviation
        """
        
        nodeFrequency = {}    
        edgeWeights = {}

        # Step 1: collect frequencies and edge co-occurrences
        for book in self.fiveStarBooks:
            for subject in book.getSubjects():
                nodeFrequency[subject] = nodeFrequency.get(subject, 0) + self.fiveStarWeight 

            # Edge weights: for each unique pair of subjects in this book, increment co-occurrence count
            for subject1, subject2 in combinations(set(book.getSubjects()), 2):
                edgeWeights[(subject1, subject2)] = edgeWeights.get((subject1, subject2), 0) + self.fiveStarWeight

        for book in self.fourStarBooks:
            for subject in book.getSubjects():
                nodeFrequency[subject] = nodeFrequency.get(subject, 0) + self.fourStarWeight

            for subject1, subject2 in combinations(set(book.getSubjects()), 2):
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

        return subjectGraph

    def subjectGraphComparator(self):
        """This method is used to compare the subject graph of the user profile with the subjects
          of the books in the database."""
        #how many of the subjects in the book are also in the user profile subject graph? 
        #and weight those subjects based on their importance in the user profile graph 
        #the weighting is based on four factors: 
        # 1) node degree - how many connections the subject has in the graph
        # 2) node weight - how important the subject is to the user based on their interactions with books that have that subject
        # 3) graph centrality - how central the subject is in the graph structure (e.g. using eigenvector centrality or betweenness centrality)
        # 4) node frequency - how many times the subject appears in the user's reading history
        pass
        