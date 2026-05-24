from src.database.library import Library
from src.services.csvImporter import CSVimporter
from src.services.dataAnalyser import DataAnalyser
from src.database.repositories.graphRepository import GraphRepository
from src.database.repositories.bookshelfRepository import BookshelfRepository
from src.database.repositories.authorsRepository import AuthorsRepository

 
class Recommender:    
    def __init__(self, csv_path = None, fiveStarWeight=1, fourStarWeight=0.7, likedAuthorWeight=0.2, ceilingFactor=1.5):
        self.validateCSVPath(csv_path)

        self.library = Library()
        self.csvImporter = CSVimporter(self.library.conn, csv_path)
        self.userID = self.csvImporter.getUserID()
        self.dataAnalyser = DataAnalyser(
            self.library.conn, self.userID, self.fiveStarWeight, self.fourStarWeight, self.ceilingFactor)
        
        self.graphRepo = GraphRepository(self.library.conn)
        self.bookshelfRepo = BookshelfRepository(self.library.conn)
        self.authorRepo = AuthorsRepository(self.library.conn)

        self.fiveStarWeight = fiveStarWeight
        self.fourStarWeight = fourStarWeight
        self.likedAuthorWeight = likedAuthorWeight
        self.ceilingFactor = ceilingFactor #number of standard deviations above the mean to set as the ceiling for node frequencies and edge weights in the subject graph
    
        self.minimumBookSimilarityThreshold = 0.5 #minimum similarity threshold for similar books (0-1)
        self.minimumUserSimilarityThreshold = 0.8 #minimum similarity threshold for similar users (0-1)

        self.finalNumberOfMatches = 10 #number of matches to return to user
        self.baseNumberOfMatches = 50 #number of matches to generate from book embedding comparison
        
        self.matches = {} #dictionary to store final matches (key: workID, value: match score)

    def recommend(self):
        #import the user's csv data and add it to the library database
        self.csvImporter.importCSV()

        #analyse the user's data to find their liked authors, create their subject graph and create their user embedding
        self.dataAnalyser.analyseUserData()

        #find similar books based on the user's five and four star bookshelves and add them to the matches dictionary with their match scores
        self.useSimilarBooks()

        #find similar users based on the user's profile embedding and add their highly rated books to the matches dictionary 
        self.useSimilarUsers()

        #graph analysis...

        #increase the match score of books written by authors the user likes
        self.useLikedAuthors()

        #increase the match scores of books with high average ratings and remove books with low average ratings
        
     
    #TODO: add better error handling and edge case handling (e.g. if user has no five star ratings, if there are no matches that meet the similarity threshold, if the CSV is in an incorrect format etc.)
    def validateCSVPath(self, csv_path):
        if csv_path is None:
            raise ValueError("CSV path cannot be None.")

    #STEP 1 - similar books   
    #fill the matches dictionary with matches and their match scores (key: workID, value: match score)
    #these matches should meet the minimum similarity threshold 
    def useSimilarBooks(self):
        """Get a list of similar books based on the user's five and four star bookshelves. 
        The top matches that meet the minimum similarity threshold are added to the matches dictionary.
        similarity score is increased for matches to five star books compared to four star books 
        based on the weights set in the constructor."""
        
        for book in self.dataAnalyser.fiveStarBookshelf :
            similarBooks = self.graphRepo.getSimilarBooks(book.getWorkID())
            top50SimilarBooks = similarBooks[:self.baseNumberOfMatches] #get the top 50 similar books
            for similarBook, similarityScore in top50SimilarBooks:
                if similarityScore >= self.minimumBookSimilarityThreshold:
                    if similarBook in self.matches:
                        self.matches[similarBook] += similarityScore * self.fiveStarWeight
                    else:
                        self.matches[similarBook] = similarityScore * self.fiveStarWeight

        for book in self.dataAnalyser.fourStarBookshelf :
            similarBooks = self.graphRepo.getSimilarBooks(book.getWorkID())
            top50SimilarBooks = similarBooks[:self.baseNumberOfMatches] #get the top 50 similar books
            for similarBook, similarityScore in top50SimilarBooks:
                if similarityScore >= self.minimumBookSimilarityThreshold:
                    if similarBook in self.matches:
                        self.matches[similarBook] += similarityScore * self.fourStarWeight
                    else:
                        self.matches[similarBook] = similarityScore * self.fourStarWeight


    #STEP 2 - similar users
    #then look at similiar users that meet the minimum usersimilarity threshold and pull their highly rated books 
    #if any of these books overlap with the matches from step 1, increase their match score by a certain amount (e.g. 10%)
    #then add to the current list of matches
    #it doesnt matter if we exceed the base number of matches at this point as we will be filtering them down later
    def useSimilarUsers(self):
        """Get a list of similar users based on the user's profile embedding. 
        The top similar users that meet the minimum similarity threshold are analysed to find their highly rated books. 
        If any of these books overlap with the matches from step 1, their match score is increased by user similarity weight. 
        These books are then added to the current list of matches.
        the more similar the user, the higher the increase in match score 
        (e.g. if a user has a similarity score of 0.8, increase the match score of their highly rated books by 0.8*userSimilarityWeight)"""
        similarUsers = self.graphRepo.getSimilarUsers(self.userID)
        for similarUser, userSimilarityScore in similarUsers:
            
            similarUserID = similarUser[0] if similarUser[0] != self.userID else similarUser[1] #get the ID of the similar user (similarUser is a tuple of (user_id_1, user_id_2))
            
            if userSimilarityScore < self.minimumUserSimilarityThreshold:
                continue

            lowestBookSimilarityScore = min(self.matches.values(), default=0)

            #for books that the similar user has rated 5 stars, increase their match score by a certain amount (relative to the user similarity score and the five star weight)
            highlyRatedBooks = self.bookshelfRepo.getRatedBooksForUser(similarUserID,5)
            for book in highlyRatedBooks:
                if book.getWorkID() in self.matches:
                    self.matches[book.getWorkID()] += userSimilarityScore * self.fiveStarWeight 
                else:
                    self.matches[book.getWorkID()] = lowestBookSimilarityScore + (userSimilarityScore * self.fiveStarWeight)
            
            #calculate match score based on the books the similar user has rated 4 stars (relative to the user similarity score and the four star weight)
            highlyRatedBooks = self.bookshelfRepo.getRatedBooksForUser(similarUserID,4)
            for book in highlyRatedBooks:
                if book.getWorkID() in self.matches:
                    self.matches[book.getWorkID()] += userSimilarityScore * self.fourStarWeight 
                else:
                    self.matches[book.getWorkID()] = lowestBookSimilarityScore + (userSimilarityScore * self.fourStarWeight)

    #STEP 3 - subject graph analysis
    #compare user subject graph to the subjects of each book in the matches
    #factor in node frequencies and edge weights in the subject graph 

    #STEP 4 - liked authors
    #then look at the authors of the matches and if any of them are in the user's liked authors, increase their match score by a certain amount (relative to the author's occurence in the liked authors)
    def useLikedAuthors(self):
        likedAuthors = self.dataAnalyser.likedAuthors
        for workID, matchScore in self.matches:
            authors = self.authorRepo.getBookAuthors(workID)
            maxWeight = -1
            for author in authors:
                if author not in likedAuthors:
                    continue
                maxWeight = max(maxWeight,likedAuthors[author])
            if maxWeight == -1:
                continue
            self.matches[workID] += maxWeight
                   
    #STEP 5 - rating analysis
    #then look at the average rating of the matches and 
        #if they are above a certain threshold (e.g. 4), increase their match score by a certain amount 
        #(relative to the rating distribution of the books in the database, 
        #e.g. if a book has a rating of 4.5 and the average rating is 3.5, increase its match score by a certain amount)
  

        
    