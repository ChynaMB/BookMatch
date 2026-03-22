from BookMatch.userProfileGraph import UserProfileGraph
from library import Library
from userProfileGraph import UserProfileGraph
from dataExtractor import DataExtractor

class Recommender:
    def __init__(self, csv_path:str):
        self.library = Library()
        self.userProfileGraph = UserProfileGraph(self.library)
        self.dataExtractor = DataExtractor(csv_path, self.library)
        self.userProfile = self.dataExtractor.createUserProfile()
        self.userID = self.userProfile.getUserID()

        self.finalNumberOfMatches = 10 #number of matches to return to user
        self.baseNumberOfMatches = 50 #number of matches to generate from book embedding comparison
        self.numOfSimilarBooks = 20 #number of similar books to retrieve from similar user matching
        self.numOfSimilarUserProfiles = 20 #number of similar user profiles to retrieve from user profile graph
        self.authorMatchWeight = 0.1 #weight to increase match score if a book is from a liked author
        self.ratingMatchWeight = 0.1 #weight to increase match score based on average rating of the book

        self.matches = {} #dictionary to store final matches (key: workID, value: match score)

    #compare user profile embedding with book embeddings in database to generate match scores
    #compare user profile embedding with other user profile embedding -> generate match score
    #pull matches from highly similar users -> generate match scores
    #if a match from similar user overlaps with match from database search -> increase its match score
    #all matches are compiled -> increase match score if they are from a liked author (relative to author occurence)
    #then use average rating of the book to change the match score (relative to the rating distribution of the books in the database, e.g. if a book has a rating of 4.5 and the average rating is 3.5, increase its match score by a certain amount)
    #then sort the matches by match score and return the top N matches
    #add user profile to database for future matching with other users

    #TODO: create similarity inclusion threshold to only include matches that are above a certain similarity score 
    # (e.g. only include books that have a match score above 0.7) - this can be applied to both book embedding comparison
    #  and similar user matching

    def generateRecommendations(self):
        #generate match scores by comparing user profile embedding and book embeddings in database
        bookMatches = self.userProfileGraph.getUserProfileSimilarBooks(self.userProfile, self.numOfSimilarBooks)

        #generate match scores by comparing user profile embedding to other user profile embeddings in database
        profileBookMatches = self.userProfileGraph.getSimilarBooksFomUserProfileMatch(self.userProfile, self.numOfSimilarUserProfiles, self.numOfSimilarBooks)    

        #combine matches from book embedding comparison and similar user matching - increase match score if a match is found in both
        combinedMatches = {}
        for workID, matchScore in bookMatches:
            if workID in profileBookMatches:
                combinedMatches[workID] = matchScore + profileBookMatches[workID]  #increase match score if found in both

        #increase match score for books from liked authors
        likedAuthors = self.userProfile.getLikedAuthors()
        for workID in combinedMatches:
            bookAuthor = self.library.getAuthorsFromBookData([workID])[0] #get author of the book
            if bookAuthor in likedAuthors:
                combinedMatches[workID] += self.authorMatchWeight * likedAuthors.count(bookAuthor)  #increase match score based on number of times author is liked

        #adjust match score based on average rating of the book
        finalMatches = {}
        for workID, matchScore in combinedMatches.items():
            averageRating = self.library.getAverageRatingsFromBookData([workID])[0]
            if averageRating is not None:
                matchScore += (averageRating * self.ratingMatchWeight)  #increase match score based on average rating of the book
            finalMatches[workID] = matchScore

        #sort matches by match score and return top N=finalNumberOfMatches matches
        sortedFinalMatches = sorted(finalMatches.items(), key=lambda x: x[1], reverse=True)
        finalMatches = {}
        for i in range(min(self.finalNumberOfMatches, len(sortedFinalMatches))):
            workID, matchScore = sortedFinalMatches[i]
            finalMatches[workID] = matchScore

        self.library.closeConnection()
        return finalMatches
        
    