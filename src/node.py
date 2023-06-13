class Node:
    id = -1
    resourceTotal = -1
    resourceLeft = -1
    dockerId = []
    resourceEmpty = []

    def __init__(self,id,resourceTotal,resourceEmpty) -> None:
        self.id = id
        self.resourceTotal = self.resourceLeft = resourceTotal
        self.resourceEmpty = resourceEmpty