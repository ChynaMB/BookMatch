from collections import Counter
from itertools import combinations
import networkx as nx
import numpy as np

class SubjectGraph:
    def __init__(self, fiveStarBooks, fourStarBooks, fiveStarWeight: float, fourStarWeight: float, ceilingFactor: float, library):
        self.fiveStarBooks = fiveStarBooks
        self.fourStarBooks = fourStarBooks
        self.fiveStarWeight = fiveStarWeight
        self.fourStarWeight = fourStarWeight
        self.ceilingFactor = ceilingFactor
        self.subjectGraph = self.createSubjectGraph()

        self.nodeFrequencyWeight = 0.5
        self.centralityWeight = 0.3
        self.edgeWeightWeight = 0.2

        self.library = self.library
        

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

    #TODO: try to break this method up into smaller methods for clarity and maintainability. 
    #TODO: Also, consider edge cases (e.g. no books, all books have the same subjects, etc.) and how to handle them.
    #TODO: Decrease the time complexity of this method by optimizing the way matches are calculated and stored.
    #TODO: Also make data retrieval more efficient 

    def subjectGraphComparator(self):
        """This method is used to compare the subject graph of the user profile with the subjects
          of the books in the database and generate match scores."""
        #how many of the subjects in the book are also in the user profile subject graph? 

        #and weight those subjects based on their importance in the user profile graph 
        #the weighting is based on three factors: 
        # 1)  node frequency - how many times the subject appears in the user's reading history
        self.nodeFrequency = {node: data['frequency'] for node, data in self.subjectGraph.nodes(data=True)}
        # 2) graph centrality - how central the subject is in the graph structure (e.g. using eigenvector centrality or betweenness centrality)
        self.eigenvectorCentrality = nx.eigenvector_centrality(self.subjectGraph, max_iter=1000) # Calculate eigenvector centrality for each node in the graph
        # 3) edge weights - how strongly the subject is connected to other subjects in the graph (e.g. using edge weights or co-occurrence counts) - this can be calculated as the sum of the weights of the edges connected to the node

        books = self.library.getAllBooks()
        matches = {}

        for book in books:
            workID = book['workID']
            subjects = book['subjects']
            for subject in subjects:
                if subject in self.subjectGraph.nodes:
                    # Calculate match score based on node frequency, eigenvector centrality, and edge weights
                    node_freq = self.nodeFrequency.get(subject, 0)
                    centrality = self.eigenvectorCentrality.get(subject, 0)
                    edge_weight_sum = sum(self.subjectGraph[subject][neighbor]['weight'] for neighbor in self.subjectGraph.neighbors(subject))
                    
                    # Combine these factors into a single match score (this is a simple example, you can experiment with different formulas)
                    match_score = node_freq * self.nodeFrequencyWeight + centrality * self.centralityWeight + edge_weight_sum * self.edgeWeightWeight
                    
                    # Store the match score for this book (you may want to aggregate scores if multiple subjects match)
                    if workID not in matches:
                        matches[workID] = match_score
                    else:
                        matches[workID] += match_score
        
        return matches
