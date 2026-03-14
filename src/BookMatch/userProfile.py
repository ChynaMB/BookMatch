class UserProfile:
    def __init__(self, userID, fiveStarBookshelf, fourStarBookshelf,  subjectGraph, likedAuthors, library):
        self.userID = userID
        self.fiveStarBookshelf = fiveStarBookshelf
        self.fourStarBookshelf = fourStarBookshelf
        self.fiveStarBooks = self.getBookWorkIDsFromBookshelf(self.fiveStarBookshelf)
        self.fourStarBooks = self.getBookWorkIDsFromBookshelf(self.fourStarBookshelf)
        self.subjectGraph = subjectGraph
        self.likedAuthors = likedAuthors
        self.userVectorEmbedding = self.createUserVectorEmbedding()
        self.matches = {} #key: bookData_id, value: match score 

        self.library = library
        self.userProfileID = library.addUserProfile(self.userID, self.fiveStarBooks, self.fourStarBooks, self.subjectGraph, self.likedAuthors, self.userVectorEmbedding)

    def getBookWorkIDsFromBookshelf(self, bookshelf):
        """given a bookshelf (list of book objects), return a list of workIDs for those books"""
        return [book.getWorkID() for book in bookshelf]

    def createUserVectorEmbedding(self):
        pass

    def updateMatches(self, matches):
        self.matches = matches
        self.library.updateUserProfileMatches(self.userProfileID, matches)

