from library import Library
from libraryGraph import LibraryGraph
from dataExtractor import DataExtractor

class Recommender:
    def __init__(self, csv_path:str):
        self.library = Library()
        self.libraryGraph = LibraryGraph(self.library)
        self.dataExtractor = DataExtractor(csv_path, self.library)
        self.userProfile = self.dataExtractor.createUserProfile()
        self.userID = self.userProfile.getUserID()
        

    #compare user profile embedding with book embeddings in database to generate match scores
    #compare user profile embedding with other user profile embedding -> generate match score
    #pull matches from highly similar users -> generate match scores
    #if a match from similar user overlaps with match from database search -> increase its match score
    #all matches are compiled -> increase match score if they are from a liked author (relative to author occurence)
    #then use average rating of the book to change the match score (relative to the rating distribution of the books in the database, e.g. if a book has a rating of 4.5 and the average rating is 3.5, increase its match score by a certain amount)
    #then sort the matches by match score and return the top N matches
    #add user profile to database for future matching with other users

    def generateRecommendations(self, finalNumberOfMatches: int = 10, baseNumberOfMatches:int = 50):
        #generate match scores based on user profile embedding and book embeddings in database
        bookMatches = self.libraryGraph.getUserProfileSimilarBooks(self.userProfile, baseNumberOfMatches)

        #generate match scores based on user profile embedding and other user profile embeddings in database
        #create userProfileClass - similar to libraryGraph but for user profiles - to handle this part of the matching process
        profileMatches = None

        #pull matches from highly similar users and generate match scores
        userProfileBookMatches = None

        #combine matches from book embedding comparison and similar user matching - increase match score if a match is found in both
        combinedMatches = None

        #increase match score for books from liked authors

        #adjust match score based on average rating of the book
        finalMatches = None

        #sort matches by match score and return top N=finalNumberOfMatches matches

        self.library.closeConnection()
        return finalMatches
        
       
