from services.subjectGraph import SubjectGraph

class UserProfile:
    def __init__(self, userID, fiveStarBooks, fourStarBooks, likedAuthors, 
                 fiveStarWeight, fourStarWeight, ceilingFactor: float, library):
        self.userID = userID
        self.fiveStarBooks = fiveStarBooks
        self.fourStarBooks = fourStarBooks
        self.likedAuthors = likedAuthors #key: author name, value: weighted occurence based on author's books in five star and four star bookshelves
      

        #TODO: use threads to parallelise the creation of the subject graph and vector embedding
        self.subjectGraph = SubjectGraph(self.fiveStarBookshelf, self.fourStarBookshelf, fiveStarWeight, fourStarWeight, ceilingFactor, library).createSubjectGraph()
        self.userVectorEmbedding = self.createUserVectorEmbedding()
        self.userProfileBookMatches = {} #key: workID, value: match score 

        self.library = library
        self.userProfileID = library.addUserProfile(self.userID, self.fiveStarBooks, self.fourStarBooks, self.subjectGraph, self.likedAuthors, self.userVectorEmbedding)

    def getBookWorkIDsFromBookshelf(self, bookshelf):
        """given a bookshelf (list of book objects), return a list of workIDs for those books"""
        return [book.getWorkID() for book in bookshelf]

    #TODO: optimse method - especially if-else statements in loops
    def createUserVectorEmbedding(self):
        """Uses the users five and four star bookshelves to create a vector embedding
        representing the user's reading preferences. This is done by averaging the vector embeddings 
        of the books in the five and four star bookshelves, with more weight given to the five star bookshelf."""
        userProfileVectorEmbedding = []
        for book in self.fiveStarBookshelf:
            for i, vectorEntry in enumerate(book.getBookVectorEmbedding()):
                if len(userProfileVectorEmbedding) == 0:
                    userProfileVectorEmbedding.append(vectorEntry * self.fiveStarWeight)
                else:
                    userProfileVectorEmbedding[i] += vectorEntry * self.fiveStarWeight
        for book in self.fourStarBookshelf:
            for i, vectorEntry in enumerate(book.getBookVectorEmbedding()):
                if len(userProfileVectorEmbedding) == 0:
                    userProfileVectorEmbedding.append(vectorEntry * self.fourStarWeight)
                else:
                    userProfileVectorEmbedding[i] += vectorEntry * self.fourStarWeight
        
        totalWeight = len(self.fiveStarBookshelf) * self.fiveStarWeight + len(self.fourStarBookshelf) * self.fourStarWeight
        if totalWeight == 0:
            return None
        
        for i in range(len(userProfileVectorEmbedding)):
            userProfileVectorEmbedding[i] = userProfileVectorEmbedding[i] / totalWeight

        return userProfileVectorEmbedding
                    
    def updateUserProfileBookMatches(self, matches):
        self.userProfileBookMatches = matches
        self.library.updateUserProfileMatches(self.userProfileID, matches)

    def getLikedAuthors(self):
        return self.likedAuthors

    def getMatches(self):
        return self.userProfileBookMatches
    
    def getUserID(self):
        return self.userID