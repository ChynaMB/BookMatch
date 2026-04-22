from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

"""
The purpose of this class is to create a graph structure that calculates and 
stores cosine similarity of books in the library. This is done to optimise the recommendation 
process by precomputing similarity scores to reduce computation time.

The graph structure will be implemented using a dictionary of dictionairies 
where the key of the outer dictionary is the work_id of a book and the value is a dictionary 
of similar books and their cosine similarity scores.

Core responsibilities of this class include:
1. Fetching book embeddings from the library and computing cosine similarity scores between books.
2. Storing the similarity scores in a graph structure for efficient retrieval during the recommendation process.
3. Storing and updating the graph structure in the library database to ensure persistence and accessibility
 for future recommendations.
4. Providing methods to retrieve similar books based on the graph structure
"""

class BookGraph:
    def __init__(self, library):
        self.library = library
        self.bookGraph = self.createBookGraph()
       
    #methods for for adding and updating graph
    def createBookGraph(self):
        """Builds the graph structure by calculating cosine similarity scores between book embeddings."""
        if self.library.isLibraryGraphInLibrary():
            return self.library.getLibraryGraph()

        bookEmbeddings = self.library.getBookEmbeddings()
        
        bookGraph = {}
        for workID1, embedding1 in bookEmbeddings.items():
            for workID2, embedding2 in bookEmbeddings.items():
                if workID1 != workID2:
                    similarity = cosine_similarity(embedding1.reshape(1, -1), embedding2.reshape(1, -1))[0][0]
                    bookGraph[workID1][workID2] = similarity
        
        self.library.addLibraryGraph(bookGraph)
        return bookGraph
    
    def addBookToGraph(self, newBook):
        """given a new Book object, calculates cosine similarity scores with existing books
          and adds it to the graph structure."""
        bookEmbeddings = self.library.getBookEmbeddings()
        newBookEmbedding = newBook.getBookVectorEmbedding()
        newBookWorkID = newBook.getWorkID()
        for workID, embedding in bookEmbeddings.items():
            similarity = cosine_similarity(newBookEmbedding.reshape(1, -1), embedding.reshape(1, -1))[0][0]
            self.bookGraph[newBookWorkID][workID] = similarity
            self.bookGraph[workID][newBookWorkID] = similarity
            self.library.addBookGraphEntry(newBookWorkID, workID, similarity)
            self.library.addBookGraphEntry(workID, newBookWorkID, similarity)

    def addBooksToGraph(self, newBooks: list):
        """given a list of Book objects, adds new books to the graph structure 
        by calculating cosine similarity scores with existing books."""
        for newBook in newBooks:
            self.addBookToGraph(newBook)

    #methods for retrieving similar books based on the graph structure
    def getSimilarBooks(self, bookWorkID, numOfSimilarBooks):
        """given a book's workID and a number, retrieves the most similar books based on cosine similarity 
        scores in the graph structure. returns a dictionary of similar book workIDs and their similarity scores."""
        if bookWorkID not in self.bookGraph:
            return []
        
        similarBooks = self.bookGraph[bookWorkID]
        sortedSimilarBooks = sorted(similarBooks.items(), key=lambda item: item[1], reverse=True)
        matches = {}
        for i in range(min(numOfSimilarBooks, len(sortedSimilarBooks))):
            workID, similarity = sortedSimilarBooks[i]
            matches[workID] = similarity
        return matches

    def getUserProfileSimilarBooks(self, userProfile, numOfSimilarBooks):
        """given a user profile and a number, retrieves the most similar books based on cosine similarity 
        scores in the graph structure. returns a dictionary of similar book workIDs and their similarity scores."""
        userEmbedding = userProfile.userVectorEmbedding
        bookEmbeddings = self.library.getBookEmbeddings()
        matchScores = {}
        for workID, bookEmbedding in bookEmbeddings.items():
            similarity = cosine_similarity(userEmbedding.reshape(1, -1), bookEmbedding.reshape(1, -1))[0][0]
            matchScores[workID] = similarity
        
        sortedMatchScores = sorted(matchScores.items(), key=lambda item: item[1], reverse=True)
        matches = {}
        for i in range(min(numOfSimilarBooks, len(sortedMatchScores))):
            workID, similarity = sortedMatchScores[i]
            matches[workID] = similarity
        return matches
