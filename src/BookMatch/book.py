class Book:
    def __init__(self, work, subjects):
        self.work = work
        self.subjects = subjects
        self.averageRating = None
        self.embedding = None
        self.bookData_id = None

    def updateAverageRating(self):
        pass

    def createEmbedding(self):
        pass

    def getBookData_idFromLibrary(self):
        pass

    def saveToLibrary(self):
        pass