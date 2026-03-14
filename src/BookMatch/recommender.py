from library import Library
from csvAnalyser import CSVAnalyser

class Recommender:
    def __init__(self, csv_path:str):
        self.library = Library()
        self.csvAnalyser = CSVAnalyser(csv_path, self.library)
        self.userProfile = self.csvAnalyser.createUserProfile()

    #compare user profile embedding with book embeddings in database to generate match scores
    #compare user profile embedding with other user profile embedding -> generate match score
    #pull matches from highly similar users -> generate match scores
    #if a match from similar user overlaps with match from database search -> increase its match score
    #all matches are compiled -> increase match score if they are from a liked author (relative to author occurence)
    