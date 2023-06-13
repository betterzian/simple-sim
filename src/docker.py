import numpy as np

class Docker:
    id = -1
    appId = -1
    nodeId = -1
    resourcePercent = 0.0

    def __init__(self,id,appId) -> None:
        self.id = id
        self.appId =appId

    def set95perResource(self,resourceRequire):
        self.resourcePercent = np.percentile(np.array(resourceRequire),95)
