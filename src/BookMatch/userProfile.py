import networkx as nx

class UserProfile:
    def __init__(self, userID, fiveStarWorks, fourStarWorks, subjectGraph, likedAuthors):
        self.userID = userID
        self.fiveStarWorks = fiveStarWorks
        self.fourStarWorks = fourStarWorks
        self.subjectGraph = subjectGraph
        self.likedAuthors = likedAuthors