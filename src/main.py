from multiprocessing import Process
import xlsxwriter as xw
import random
import csv
import app
import docker
import node
import math
import numpy as np



def run(appList, dockerList, nodeList, flag):
    if flag == "greedy":
        schedule1(appList, dockerList, nodeList)
    elif flag == "probability1":
        schedule2(appList, dockerList, nodeList)
    elif flag == "probability2":
        schedule3(appList, dockerList, nodeList)
    elif flag == "normal":
        schedule4(appList, dockerList, nodeList)
    UR = caculateUtilizationRate(appList, dockerList, nodeList)
    writeToExcel(UR, appList, dockerList, nodeList, flag)


def schedule1(appList, dockerList, nodeList):  # greedy
    for nowDocker in dockerList:
        nowPriority = 99999999.0
        nowSelect = -1
        for nowNode in nodeList:
            enough, priority = compare(appList[nowDocker.appId].resourceRequire, nowNode.resourceEmpty)
            if enough and priority < nowPriority:
                nowPriority = priority
                nowSelect = nowNode
        if nowSelect != -1:
            updateNode(appList, nowDocker, nowSelect)
            updateDocker(appList, nowDocker, nowSelect)


def schedule2(appList, dockerList, nodeList):
    beta = [[0 for _ in range(98)] for _ in range(98)]
    for elem in dockerList:
        for i in range(math.ceil(np.percentile(np.array(appList[elem.appId].resourceRequire[0:48]),100)),98):
            for j in range(math.ceil(np.percentile(np.array(appList[elem.appId].resourceRequire[48:]),100)),98):
                beta[i][j] += 1
    print("beta初始化完成")
    count = 0
    for nowDocker in dockerList:
        nowPriority = 99999999.0
        nowSelect = -1
        nowBeta = 9999999.9
        betaList = []
        for nowNode in nodeList:
            enough, priority, betaList= compare2(appList[nowDocker.appId].resourceRequire, nowNode.resourceEmpty)
            if enough:
                if (beta[betaList[0]][betaList[1]] * 1.0 / beta[97][97]) > 0.6:
                    nowSelect = nowNode
                    break
                elif beta[betaList[0]][betaList[1]] > nowBeta:
                    nowBeta = beta[betaList[0]][betaList[1]]
                    nowSelect = nowNode
                elif beta[betaList[0]][betaList[1]] == nowBeta and priority < nowPriority:
                    nowPriority = priority
                    nowSelect = nowNode

        if nowSelect != -1:
            updateNode(appList, nowDocker, nowSelect)
            updateDocker(appList, nowDocker, nowSelect)
            count += 1
            for i in range(betaList[0],98):
                for j in range(betaList[1],98):
                    beta[i][j] -= 1
        if count % 1000 == 0:
            print(str(count)+"  1")

def schedule3(appList, dockerList, nodeList):
    beta = [[0 for _ in range(98)] for _ in range(98)]
    nodeLeftOrRight = [0 for _ in range(len(nodeList))]

    for elem in dockerList:
        for i in range(math.ceil(np.percentile(np.array(appList[elem.appId].resourceRequire[0:48]),100)),98):
            for j in range(math.ceil(np.percentile(np.array(appList[elem.appId].resourceRequire[48:]),100)),98):
                beta[i][j] += 1
    print("beta初始化完成")
    count = 0
    temp = 0
    for nowDocker in dockerList:
        nowPriority = 99999999.0
        nowSelect = -1
        nowBeta = 9999999.9
        betaList = []
        for nowNode in nodeList:
            enough, priority, betaList = compare2(appList[nowDocker.appId].resourceRequire, nowNode.resourceEmpty)
            if enough:
                if betaList[1] <= (betaList[0]/1.5):
                    if nodeLeftOrRight[nowNode.id] < -1:
                        continue
                    temp = 0 - math.ceil(betaList[0]/betaList[1])
                if (betaList[1]/1.5) >= betaList[0]:
                    if nodeLeftOrRight[nowNode.id] > -1:
                        continue
                    temp = math.ceil(betaList[1]/betaList[0])

                if (beta[betaList[0]][betaList[1]] * 1.0 / beta[97][97]) > 0.6:
                    nowSelect = nowNode
                    break
                if beta[betaList[0]][betaList[1]] > nowBeta:
                    nowBeta = beta[betaList[0]][betaList[1]]
                    nowSelect = nowNode
                elif beta[betaList[0]][betaList[1]] == nowBeta and priority < nowPriority:
                    nowPriority = priority
                    nowSelect = nowNode

        if nowSelect != -1:
            updateNode(appList, nowDocker, nowSelect)
            updateDocker(appList, nowDocker, nowSelect)
            nodeLeftOrRight[nowSelect.id] += temp
            count += 1
            for i in range(betaList[0],98):
                for j in range(betaList[1],98):
                    beta[i][j] -= 1
        if count % 1000 == 0:
            print(str(count)+"   2")

def schedule4(appList, dockerList, nodeList):
    for item in dockerList:
        item.set95perResource(appList[item.appId].resourceRequire)
    for nowDocker in dockerList:
        nowPriority = 99999999.0
        nowSelect = -1
        for nowNode in nodeList:
            temp = nowNode.resourceLeft - nowDocker.resourcePercent
            if temp >= 0 and nowPriority > temp:
                nowPriority = temp
                nowSelect = nowNode
        if nowSelect != -1:
            nowSelect.resourceLeft = nowPriority
            updateNode(appList, nowDocker, nowSelect)
            updateDocker(appList, nowDocker, nowSelect)


def caculateUtilizationRate(appList, dockerList, nodeList):
    resourceTotal = 0.0
    resourceEmpty = 0.0
    resource = 0.0
    for tempNode in nodeList:
        for temp in tempNode.resourceEmpty:
            resourceTotal = resourceTotal + tempNode.resourceTotal
            resourceEmpty = resourceEmpty + temp
    num = 0
    for tempDocker in dockerList:
        if tempDocker.nodeId != -1:
            num = num + 1
    return [(resourceTotal - resourceEmpty) / resourceTotal, num, len(dockerList)]


def writeToExcel(UR, appList, dockerList, nodeList, flag):
    workbook = xw.Workbook("../data/output/"+flag + "_output.xlsx")  # 创建工作簿
    worksheet1 = workbook.add_worksheet("docker_node")  # 创建子表
    worksheet1.activate()  # 激活表
    URdate = [flag]
    URdate.extend(UR)
    worksheet1.write_row('A1', URdate)
    title = ['算法', '容器', '机器']  # 设置表头
    worksheet1.write_row('A2', title)  # 从A1单元格开始写入表头
    i = 3  # 从第三行开始写入数据
    for temp in dockerList:
        insertData = [flag, temp.id, temp.nodeId]
        row = 'A' + str(i)
        worksheet1.write_row(row, insertData)
        i += 1
    # worksheet2 = workbook.add_worksheet("node_docker")  # 创建子表
    # worksheet2.activate()
    # URdate = [flag]
    # URdate.extend(UR)
    # worksheet2.write_row('A1',URdate)
    # title = ['算法','机器','数量','容器']
    # worksheet2.write_row('A2', title)
    # i = 3
    # for temp in nodeList:
    #     insertData = [flag,temp.id,len(temp.dockerId)]
    #     insertData.extend(temp.dockerId)
    #     row = 'A' + str(i)
    #     worksheet2.write_row(row, insertData)
    #     i += 1
    workbook.close()  # 关闭表    


def compare(resourceRequire, resourceEmpty):
    priorty = 0.0
    for i in range(len(resourceRequire)):
        if resourceRequire[i] > resourceEmpty[i]:
            return False, 0
        priorty = resourceEmpty[i] - resourceRequire[i] + priorty
    return True, priorty


def compare2(resourceRequire, resourceEmpty):
    newList = []
    priority = 0.0
    for i in range(len(resourceRequire)):
        if resourceRequire[i] > resourceEmpty[i]:
            return False, 0, []
        temp = resourceEmpty[i] - resourceRequire[i]
        newList.append(temp)
        priority = temp + priority
    tempList = [math.ceil(np.percentile(np.array(newList[0:48]),0)),math.ceil(np.percentile(np.array(newList[48:]),0))]
    return True, priority, tempList

# def compare3(resourceRequire, resourceEmpty):
#     newList = []
#     priority = 0.0
#     for i in range(len(resourceRequire)):
#         if resourceRequire[i] > resourceEmpty[i]:
#             return False, 0, []
#         temp = resourceEmpty[i] - resourceRequire[i]
#         newList.append(temp)
#         priority = temp + priority
#     tempList = [math.ceil(np.percentile(np.array(newList[0:48]),100)),math.ceil(np.percentile(np.array(newList[48:]),100))]
#     return True, priority, tempList

def updateNode(appList, nowDocker, nowNode):
    nowNode.dockerId.append(nowDocker.id)
    for i in range(len(nowNode.resourceEmpty)):
        nowNode.resourceEmpty[i] = nowNode.resourceEmpty[i] - appList[nowDocker.appId].resourceRequire[i]
        if nowNode.resourceEmpty[i] < 0:
            nowNode.resourceEmpty[i] = 0


def updateDocker(appList, nowDocker, nowNode):
    nowDocker.nodeId = nowNode.id


if __name__ == "__main__":
    appList = [-1]
    dockerList = []
    nodeList = []
    csv_reader = csv.reader(open("../data/source/docker-data.csv"))
    i = 1
    for line in csv_reader:
        tempNum = line[1].split("|")
        tempNum = list(map(float, tempNum))
        appList.append(app.App(i, tempNum))
        i = i + 1
    csv_reader = csv.reader(open("../data/source/node-data.csv"))
    i = 1
    timeBlockCount = len(appList[1].resourceRequire)
    for line in csv_reader:
        if random.random() < 0.58:
            continue
        tempList = []
        for tempI in range(timeBlockCount):
            tempList.append(float(line[1]))
        nodeList.append(node.Node(i, float(line[1]), tempList))
        i = i + 1
    csv_reader = csv.reader(open("../data/source/docker-app.csv"))
    for line in csv_reader:
        appId = line[1].split("_")
        dockerId = line[0].split("_")
        dockerList.append(docker.Docker(int(dockerId[1]), int(appId[1])))

    p1 = Process(target=run, args=(appList, dockerList, nodeList, "greedy"))  # 实例化进程对象
    p2 = Process(target=run, args=(appList, dockerList, nodeList, "probability1"))  # 实例化进程对象
    p3 = Process(target=run, args=(appList, dockerList, nodeList, "probability2"))  # 实例化进程对象
    p4 = Process(target=run, args=(appList, dockerList, nodeList, "normal"))  # 实例化进程对象
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p1.join()
    p2.join()
    p3.join()
    p4.join()
