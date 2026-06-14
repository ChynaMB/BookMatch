from src.database.library import Library
from src.services.csvImporter import CSVimporter
from src.services.dataAnalyser import DataAnalyser
from src.repositories.graphRepository import GraphRepository
from src.repositories.bookshelfRepository import BookshelfRepository
from src.repositories.subjectsRepository import SubjectsRepository
from src.repositories.authorsRepository import AuthorsRepository
from src.repositories.booksRepository import BooksRepository
from src.repositories.libraryDataRepository import LibraryDataRepository
from src.repositories.matchesRepository import MatchesRepository
import networkx as nx

class Recommender:    
    def __init__(self, file_contents = None):
        self.file_contents = file_contents
        self.validateFileContents()

        self.fiveStarWeight = 1
        self.fourStarWeight = 0.7
        self.likedAuthorWeight = 0.2
        self.ratingWeight = 0.2
        
        self.ceilingFactor = 1.5 #number of standard deviations above the mean to set as the ceiling for node frequencies and edge weights in the subject graph
        self.nodeFrequencyWeight = 0.5
        self.centralityWeight = 0.3
        self.edgeWeightWeight = 0.2

        self.minimumBookSimilarityThreshold = 0.5 #minimum similarity threshold for similar books (0-1)
        self.minimumUserSimilarityThreshold = 0.8 #minimum similarity threshold for similar users (0-1)
        self.averageRatingBaseline = 3.8
        self.minimumAverageRating = 3.0

        self.baseNumberOfMatches = 100 #number of matches to initially generate using embeddings and graohs
        self.finalNumberOfMatches = 10 #number of matches to return to user

        self.library = Library()
        self.csvImporter = CSVimporter(self.library.conn, file_contents)
        self.userID = self.csvImporter.getUserID()
        self.dataAnalyser = DataAnalyser(
            self.library.conn, self.userID, self.fiveStarWeight, self.fourStarWeight, self.ceilingFactor)
        
        self.graphRepo = GraphRepository(self.library)
        self.bookshelfRepo = BookshelfRepository(self.library)
        self.subjectsRepo = SubjectsRepository(self.library)
        self.authorRepo = AuthorsRepository(self.library)
        self.booksRepo = BooksRepository(self.library)
        self.libraryDataRepo = LibraryDataRepository(self.library)
        self.matchesRepository = MatchesRepository(self.library)

        self.matches = {} # key: work_id, value: match score
        self.finalMatches = []

    #TODO: add better error handling and edge case handling (e.g. if user has no five star ratings, if there are no matches that meet the similarity threshold, if the CSV is in an incorrect format etc.)
    def recommend(self):
        #import the user's csv data and add it to the library database
        self.csvImporter.importCSV()

        #analyse the user's data to find their liked authors, create their subject graph and create their user embedding
        self.dataAnalyser.analyseUserData()

        #find similar books based on the user's five and four star bookshelves and add them to the matches dictionary with their match scores
        self.useSimilarBooks()

        #find similar users based on the user's profile embedding and add their highly rated books to the matches dictionary 
        self.useSimilarUsers()

        #compare user subject graph to the subjects of each book in the matches
        self.useSubjectGraph()

        #reduce number of matches
        self.finalMatches = self.reduceMatches(self.baseNumberOfMatches)

        #increase the match score of books written by authors the user likes
        self.useLikedAuthors()

        #increase the match scores of books with high average ratings and remove books with low average ratings
        self.useAverageRating()

        #add matches to the database
        self.addMatches()

        #get final matches
        userMatches = self.getFinalMatches()

        return userMatches #list of dicts with title, authors, matchScore
     
    #TODO: add a check to make sure file is a csv
    def validateFileContents(self):
        if not self.file_contents:
            raise ValueError("File contents cannot be empty.")

    def isValidReccomendation(self, workID):
        """return true if the book is not in the 'Read' shelf or 'Did Not Finish' shelf and false otherwise"""
        shelf = self.bookshelfRepo.whichShelfIsBookOnForUser(self.dataAnalyser.userID, workID)
        return shelf not in ['Read', 'Did Not Finish']


    #STEP 1 - similar books   
    #fill the matches dictionary with matches and their match scores (key: workID, value: match score)
    #these matches should meet the minimum similarity threshold 
    #TODO: optimise this method by reducing the number of database calls and simplifying the logic. 
        #For example, instead of getting the similar books for each book in the user's bookshelf and then filtering them, 
        #we could get all similar books for all books in the user's bookshelf in one query and then filter them in memory. 
        #This would reduce the number of database calls and simplify the logic.
    def useSimilarBooks(self):
        """Get a list of similar books based on the user's five and four star bookshelves. 
        The top matches that meet the minimum similarity threshold are added to the matches dictionary.
        similarity score is increased for matches to five star books compared to four star books 
        based on the weights set in the constructor."""
        
        for book in self.dataAnalyser.fiveStarBookshelf:
            self._addSimilarBooksForSeed(book.getWorkID(), self.fiveStarWeight)

        for book in self.dataAnalyser.fourStarBookshelf:
            self._addSimilarBooksForSeed(book.getWorkID(), self.fourStarWeight)

    def _addSimilarBooksForSeed(self, seed_work_id, weight):
        similar_books = self.graphRepo.getSimilarBooks(seed_work_id)
        for work_id, similarity_score in similar_books:
            if similarity_score < self.minimumBookSimilarityThreshold:
                break

            if not self.isValidReccomendation(work_id):
                continue

            if work_id in self.matches:
                continue

            self.matches[work_id] = similarity_score * weight


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
        similar_users = self.graphRepo.getSimilarUsers(self.userID)
        lowest_book_similarity_score = min(self.matches.values(), default=0)

        for similar_user_id, user_similarity_score in similar_users:
            if user_similarity_score < self.minimumUserSimilarityThreshold:
                break

            self._addHighlyRatedBooksFromUser(
                similar_user_id,
                5,
                user_similarity_score,
                self.fiveStarWeight,
                lowest_book_similarity_score,
            )
            self._addHighlyRatedBooksFromUser(
                similar_user_id,
                4,
                user_similarity_score,
                self.fourStarWeight,
                lowest_book_similarity_score,
            )

    def _addHighlyRatedBooksFromUser(
        self,
        user_id,
        rating,
        user_similarity_score,
        rating_weight,
        lowest_book_similarity_score,
    ):
        highly_rated_books = self.bookshelfRepo.getRatedBooksForUser(user_id, rating)
        score_delta = user_similarity_score * rating_weight

        for book in highly_rated_books:
            work_id = book.getWorkID()
            if work_id in self.matches:
                self.matches[work_id] += score_delta
            else:
                self.matches[work_id] = lowest_book_similarity_score + score_delta

    #STEP 3 - subject graph analysis
    #compare user subject graph to the subjects of each book in the matches
    #factor in node frequencies and edge weights in the subject graph 
    #TODO: try to break this method up into smaller methods for clarity and maintainability. 
    #TODO: Also, consider edge cases (e.g. no books, all books have the same subjects, etc.) and how to handle them.
    #TODO: Decrease the time complexity of this method by optimizing the way matches are calculated and stored.
    #TODO: Also make data retrieval more efficient 
    def useSubjectGraph(self):
        """Compare the user's subject graph to candidate book subjects and add subject-based scores."""
        subject_graph = self.dataAnalyser.subjectGraph
        if subject_graph is None or subject_graph.number_of_nodes() == 0:
            return

        node_frequency = {node: data['frequency'] for node, data in subject_graph.nodes(data=True)}
        eigenvector_centrality = nx.eigenvector_centrality(subject_graph, max_iter=1000)

        for work_id in list(self.matches.keys()):
            subjects = self.subjectsRepo.getBookSubjects(work_id)
            for subject in subjects:
                if subject not in subject_graph.nodes:
                    continue

                node_freq = node_frequency.get(subject, 0)
                centrality = eigenvector_centrality.get(subject, 0)
                edge_weight_sum = sum(
                    subject_graph[subject][neighbor]['weight']
                    for neighbor in subject_graph.neighbors(subject)
                )

                match_score = (
                    node_freq * self.nodeFrequencyWeight
                    + centrality * self.centralityWeight
                    + edge_weight_sum * self.edgeWeightWeight
                )
                self.matches[work_id] += match_score

    #STEP 4 - reduce the number of matches
    #reduce the number of matches at this stage for effienciency purposes.
    #we have used the data to find the best matches
    #any other thing done to the matches is to diffentiate between them
    #not to find different matches
    def reduceMatches(self, numOfMAtches) -> list:
        sorted_matches = sorted(self.matches.items(), key=lambda x: x[1], reverse=True)
        return sorted_matches[:numOfMAtches] #list of tuples (work_id, match score)
        
        
    #STEP 5 - liked authors
    #then look at the authors of the matches and if any of them are in the user's liked authors, increase their match score by a certain amount (relative to the author's occurence in the liked authors)
    def useLikedAuthors(self):
        liked_authors = self.dataAnalyser.likedAuthors
        for i, (work_id, match_score) in enumerate(self.finalMatches):
            authors = self.authorRepo.getBookAuthors(work_id)

            max_weight = -1
            for author in authors:
                if author not in liked_authors:
                    continue
                max_weight = max(max_weight, liked_authors[author])

            if max_weight == -1:
                continue

            self.finalMatches[i] = (
                work_id,
                match_score + (max_weight * self.likedAuthorWeight),
            )

    #STEP 6 - rating analysis
    #then look at the average rating of the matches and 
    #if they are above a certain threshold (e.g. 4), increase their match score by a certain amount 
    #relative to the rating distribution of the books in the database, 
    #e.g. if a book has a rating of 4.5 and the average rating is 3.5, increase its match score by a certain amount)
    def useAverageRating(self):
        """
        Boost match scores for books rated above the library average.
        The boost is proportional to how far the book's rating exceeds the baseline.
        """
        average_rating_in_library = self.libraryDataRepo.getAverageBooksRating() or 0
        baseline_rating = max(self.averageRatingBaseline, average_rating_in_library)

        to_be_deleted = []
        for i, (work_id, match_score) in enumerate(self.finalMatches):
            rating = self.booksRepo.getAverageBookRating(work_id)
            if not rating:
                to_be_deleted.append(work_id)
                continue

            if rating < self.minimumAverageRating:
                to_be_deleted.append(work_id)
                continue

            if rating < baseline_rating:
                continue

            difference = rating - baseline_rating
            self.finalMatches[i] = (work_id, match_score + (self.ratingWeight * difference))
            
        if to_be_deleted:
            deleted = set(to_be_deleted)
            self.finalMatches = [
                match for match in self.finalMatches if match[0] not in deleted
            ]

    #STEP 7 - add user matches to the database
    def addMatches(self):
        matches = [(self.userID, work_id, match_score) for work_id, match_score in self.finalMatches]
        self.matchesRepository.insertMatches(matches)

    #STEP 8 - get the final matches
    def getFinalMatches(self) -> list:
        sorted_final_matches = sorted(self.finalMatches, key=lambda x: x[1], reverse=True)
        top_matches = sorted_final_matches[:self.finalNumberOfMatches]

        user_matches = []
        for work_id, match_score in top_matches:
            book = self.booksRepo.getBookByWorkID(work_id)
            if book is None:
                continue

            user_matches.append({
                "title": book.getTitle(),
                "authors": self.authorRepo.getBookAuthors(work_id),
                "matchScore": match_score,
            })

        return user_matches
