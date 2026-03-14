import networkx as nx
import json

class UserProfile:
    def __init__(self, userID, fiveStarBookshelf, fourStarBookshelf, fiveStarWorks, fourStarWorks, likedAuthors, library):
        self.userID = userID
        self.fiveStarBookshelf = fiveStarBookshelf
        self.fourStarBookshelf = fourStarBookshelf
        self.fiveStarWorks = fiveStarWorks
        self.fourStarWorks = fourStarWorks
        self.likedAuthors = likedAuthors
        self.userVectorEmbedding = self.createUserVectorEmbedding()
        #self.userStringEmbedding = json.dumps(self.userVectorEmbedding.tolist()) #convert numpy array to list, then to string for database storage
        self.matches = {} #key: bookData_id, value: match score 
        self.library = library    

    def createUserVectorEmbedding(self):
        pass