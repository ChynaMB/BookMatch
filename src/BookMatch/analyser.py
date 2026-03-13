from itertools import combinations
import requests
import networkx as nx
from userProfile import UserProfile
from BookMatch.book import BookEmbedder

class Analyser:
    def __init__(self, userID, csvDataFrame, Library):
        self.userID = userID
        self.library = Library
        self.openLibraryURL = "https://openlibrary.org"
        self.fiveStarISBNS = csvDataFrame[csvDataFrame['My Rating'] == 5]
        self.fourStarISBNS = csvDataFrame[csvDataFrame['My Rating'] == 4]
        self.fiveStarAuthors = self.fiveStarISBNS['Author'].tolist()
        self.fourStarAuthors = self.fourStarISBNS['Author'].tolist()
        self.fiveStarWeight = 2
        self.fourStarWeight = 1
        
    def getWorksFromISBNS(self, ISBNS: list) -> tuple[list, list]:
        """Given a list of ISBNs, return a list of works (work ID)
        we use wworks instead of isbn because some books have multiple editions with different ISBNs, 
        but they all belong to the same work"""
        works = set() #use a set to avoid duplicates
        failed_isbns = [] #keep track of failed ISBNs for debugging

        print(f"Getting works for ISBNs")
        for isbn in ISBNS:
            url = f"{self.openLibraryURL}/isbn/{isbn}.json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for ISBN {isbn}: {response.status_code}")
                failed_isbns.append(isbn)
                continue
            
            data = response.json()
            
            if "works" in data:
                workID = data["works"][0]["key"] #example:/works/OL45883W
                works.add(workID)
            else:
                print(f"No work found for ISBN {isbn}")
                failed_isbns.append(isbn)

        return list(works), failed_isbns
    
    def getSubjectsFromWorks(self, works: list) -> tuple[dict, list]:
        """Given a list of works, return a dictionary of workID to subjects"""
        work_subjects = {} #key: workID, value: list of subjects
        failed_works = []

        print(f"Getting subjects for works")
        for work in works:
            url = f"{self.openLibraryURL}{work}.json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for work {work}: {response.status_code}")
                failed_works.append(work)
                continue
            
            data = response.json()
            
            if "subjects" in data:
                subjects = data["subjects"]
                work_subjects[work] = subjects
            else:
                print(f"No subjects found for work {work}")
                failed_works.append(work)

        return work_subjects, failed_works
    
    def getSubjectGraph(self, work_subjects: dict, weightMultiplier: float) -> nx.Graph:
        """
        Given a dictionary of workID to subjects, return/update a graph showing two thing:
        1) the frequency of each subject amongst all works
        2) The relationships between subjects for each work, where the weight of the edge is weighted 
            by their occurence together in the same work
        """
        
        subjectGraph = nx.Graph()

        for subjects in work_subjects.values():
            #increment frequency for each subject
            for subj in subjects:
                if subjectGraph.has_node(subj):
                    subjectGraph.nodes[subj]['frequency'] += weightMultiplier
                else:
                    subjectGraph.add_node(subj, frequency=1)

            #increment edge weight for each pair of subjects that occur together
            for subj1, subj2 in combinations(subjects, 2):
                if subjectGraph.has_edge(subj1, subj2):
                    subjectGraph[subj1][subj2]['weight'] += weightMultiplier
                else:
                    subjectGraph.add_edge(subj1, subj2, weight=weightMultiplier)

        return subjectGraph
    
    def updateSubjectGraph(self, subjects, subjectGraph: nx.Graph, weightMultiplier: float) -> nx.Graph:
        """Given a list of subjects for a work, update the subject graph with the new subjects and their relationships"""
        for subj in subjects:
            if subjectGraph.has_node(subj):
                subjectGraph.nodes[subj]['frequency'] += weightMultiplier
            else:
                subjectGraph.add_node(subj, frequency=1)

        for subj1, subj2 in combinations(subjects, 2):
            if subjectGraph.has_edge(subj1, subj2):
                subjectGraph[subj1][subj2]['weight'] += weightMultiplier
            else:
                subjectGraph.add_edge(subj1, subj2, weight=weightMultiplier)

        return subjectGraph

    def getLikedAuthors(self):
        """Return a dictionairy of liked authors based on the frequency of authors in the 4 and 5 star ratings"""
        authorFrequency = {}

        for author in self.fiveStarAuthors:
            if author in authorFrequency:
                authorFrequency[author] += self.fiveStarWeight
            else:
                authorFrequency[author] = 1

        for author in self.fourStarAuthors:
            if author in authorFrequency:      
                authorFrequency[author] +=  self.fourStarWeight
            else:
                authorFrequency[author] = 1

        #return a new dictionary with only authors that have a frequency greater than 1
        return {author: freq for author, freq in authorFrequency.items() if freq > 1}

    #TODO: createBook and createUserProfile can be done in parallel with threading since they are independent of each other
    def createBook(self, works, subjects):
        """Given a list of works, check library.db to see if we have a submition for each work
        if not, create a Book for it so it can be stored in the library"""
        for work in works:
            #check if book already exists in library.db
            #if not, create a new Book and store it in library.db
            pass

    #TODO: CREATE THREADING FOR THIS FUNCTION
    def createUserProfile(self) -> UserProfile:
        """Create a user profile based on the subject graph"""
        fiveStarWorks, failed_5star_ISBNS = self.getWorksFromISBNS(self.fiveStarISBNS['ISBN'].tolist())
        fiveStarSubjects, failed_5star_works = self.getSubjectsFromWorks(fiveStarWorks)
        fourStarWorks, failed_4star_ISBNS = self.getWorksFromISBNS(self.fourStarISBNS['ISBN'].tolist())
        fourStarSubjects, failed_4star_works = self.getSubjectsFromWorks(fourStarWorks)

        #weigh 5 star subjects more than 4 star subjects
        subjectGraph = self.getSubjectGraph(fiveStarSubjects, self.fiveStarWeight) 
        for subjects in fourStarSubjects.values():
            subjectGraph = self.updateSubjectGraph(subjects, subjectGraph, self.fourStarWeight)

        likedAuthors = self.getLikedAuthors()
        
        return UserProfile(self.userID, fiveStarWorks, fourStarWorks, subjectGraph, likedAuthors)