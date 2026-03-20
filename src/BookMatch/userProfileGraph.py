from bookGraph import BookGraph
from sklearn.metrics.pairwise import cosine_similarity

#This class extends the functionality of the BookGraph class to create a UserGraph class that 
# calculates and stores cosine similarity of user profiles in the library. 
# This is done to optimise the recommendation process by precomputing similarity scores to reduce computation time.

class UserProfileGraph(BookGraph):
    def __init__(self, library):
        super().__init__(library)
        self.userProfileGraph = self.createUserProfileGraph()

    def createUserProfileGraph(self):
        """Builds the graph structure by calculating cosine similarity scores between user profile embeddings."""
        if self.library.isUserProfileGraphInLibrary():
            return self.library.getUserProfileGraph()

        userProfileEmbeddings = self.library.getUserProfileEmbeddings()

        userProfileGraph = {}
        for userID1, embedding1 in userProfileEmbeddings.items():
            for userID2, embedding2 in userProfileEmbeddings.items():
                if userID1 != userID2:
                    similarity = cosine_similarity(embedding1.reshape(1, -1), embedding2.reshape(1, -1))[0][0]
                    userProfileGraph[userID1][userID2] = similarity

        self.library.addUserProfileGraph(userProfileGraph)
        return userProfileGraph
    
    def addUserProfileToGraph(self, newUserProfile):
        """given a new UserProfile object, calculates cosine similarity scores with existing user profiles
          and adds it to the graph structure."""
        userProfileEmbeddings = self.library.getUserProfileEmbeddings()
        newUserProfileEmbedding = newUserProfile.getUserProfileVectorEmbedding()
        newUserID = newUserProfile.getUserID()
        for userID, embedding in userProfileEmbeddings.items():
            similarity = cosine_similarity(newUserProfileEmbedding.reshape(1, -1), embedding.reshape(1, -1))[0][0]
            self.userProfileGraph[newUserID][userID] = similarity
            self.userProfileGraph[userID][newUserID] = similarity
            self.library.addUserProfileGraphEntry(newUserID, userID, similarity)
            self.library.addUserProfileGraphEntry(userID, newUserID, similarity)

    def addUserProfilesToGraph(self, newUserProfiles: list):
        """given a list of UserProfile objects, adds new user profiles to the graph structure 
        by calculating cosine similarity scores with existing user profiles."""
        for newUserProfile in newUserProfiles:
            self.addUserProfileToGraph(newUserProfile)

    #
    def getSimilarUserProfiles(self, userProfile, numberOfSimilarUserProfiles):
        """given a user profile, retrieves similar user profiles based on cosine similarity scores between the user profile embedding and other user profile embeddings in the database."""
        userProfileEmbedding = userProfile.getUserProfileVectorEmbedding()
        userID = userProfile.getUserID()
        if userID not in self.userProfileGraph:
            raise Exception("User profile not found in graph")
        
        similarUserProfiles = self.userProfileGraph[userID]
        sortedSimilarUserProfiles = sorted(similarUserProfiles.items(), key=lambda x: x[1], reverse=True)
        matches = {}
        for i in range(min(numberOfSimilarUserProfiles, len(sortedSimilarUserProfiles))):
            similarUserID, similarityScore = sortedSimilarUserProfiles[i]
            matches[similarUserID] = similarityScore
        return matches
        
    def getSimilarBooksFomUserProfileMatch(self, userProfile, numberOfSimilarUserProfiles, numberOfSimilarBooks):
        """given a user profile, retrieves similar books based on cosine similarity scores
          between the user profile embedding and book embeddings in the database. returns a dictionary
            of book work IDs and their corresponding similarity scores."""
        userProfileEmbedding = userProfile.getUserProfileVectorEmbedding()
        similarUserProfiles = self.getSimilarUserProfiles(userProfile, numberOfSimilarUserProfiles)
        similarBooks = {}
        for userProfileID, similarity in similarUserProfiles.items():
            userProfileBooks = self.library.getUserProfileBooks(userProfileID)
            for workID in userProfileBooks:
                if workID not in similarBooks:
                    similarBooks[workID] = similarity
                else:
                    similarBooks[workID] += similarity
        sortedSimilarBooks = sorted(similarBooks.items(), key=lambda x: x[1], reverse=True)
        matches = {}
        for i in range(min(numberOfSimilarBooks, len(sortedSimilarBooks))):
            workID, similarityScore = sortedSimilarBooks[i]
            matches[workID] = similarityScore
        return matches

       
