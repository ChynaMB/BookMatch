import networkx as nx

class UserProfile:
    def __init__(self, userID, bookShelf, fiveStarWorks, fourStarWorks, subjectGraph, likedAuthors):
        self.userID = userID
        self.bookshelf = bookShelf
        self.fiveStarWorks = fiveStarWorks
        self.fourStarWorks = fourStarWorks
        self.subjectGraph = subjectGraph
        self.likedAuthors = likedAuthors