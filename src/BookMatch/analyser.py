import requests
import networkx as nx
from bookEmbedder import BookEmbedder

class Analyser:
    def __init__(self, csvDataFrame):
        self.openLibraryURL = "https://openlibrary.org"
        self.fiveStarISBNS = csvDataFrame[csvDataFrame['My Rating'] == 5]
        self.fourStarISBNS = csvDataFrame[csvDataFrame['My Rating'] == 4]
        

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
    
    def getSubjectGraph(self, work_subjects: dict) -> nx.Graph:
        """
        Given a dictionary of workID to subjects, return a graph showing two thing:
        1) the frequency of each subject amongst all works
        2) The relationships between subjects for each work, where the weight of the edge is weighted 
            by their occurence together in the same work
        """
        subjectGraph = nx.Graph()

        for subjects in work_subjects.values():
            #increment frequency for each subject
            for subj in subjects:
                if subjectGraph.has_node(subj):
                    subjectGraph.nodes[subj]['frequency'] += 1
                else:
                    subjectGraph.add_node(subj, frequency=1)

            #increment edge weight for each pair of subjects that occur together
            for i, subj1 in enumerate(subjects):
                for subj2 in subjects[i+1:]:
                    if subjectGraph.has_edge(subj1, subj2):
                        subjectGraph[subj1][subj2]['weight'] += 1
                    else:
                        subjectGraph.add_edge(subj1, subj2, weight=1)

        return subjectGraph

    def addWorksToGraph(self, graph: nx.Graph, work_subjects: dict) -> nx.Graph:
        """Add works as nodes to the graph and connect them to their subjects"""
        for workID, subjects in work_subjects.items():
            graph.add_node(workID, type='work')
            for subj in subjects:
                graph.add_edge(workID, subj, weight=1)
        
        return graph