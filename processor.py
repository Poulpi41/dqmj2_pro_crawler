import json
import threading
import bs4
import re

def path(name:str,pageNum:int):
    return f"./res/{name}/synths_{pageNum}.html"
def treatText(text:str) -> str:
    return re.sub(r"\s+", " ", text).replace("\n", "").strip().lower()
def treat1File(name:str,pageNum:int,res:set,mutex:threading.Lock):
    with open(path(name,pageNum), 'r') as f:
        soup:bs4.BeautifulSoup = bs4.BeautifulSoup(f.read(), 'html.parser')
    all_tr:bs4.BeautifulSoup = soup.find_all('tr')
    all_tr = all_tr[1:]
    for row in all_tr:
        all_td = row.find_all('td')
        son     = treatText(all_td[0].text)
        father1 = treatText(all_td[2].text)
        father2 = treatText(all_td[4].text)
        father3 = treatText(all_td[6].text)
        father4 = treatText(all_td[8].text)
        synth = treatText(all_td[9].text)
        rank = treatText(all_td[10].text)
        with mutex:
            res.add(tuple([son,father1,father2,father3,father4,synth,rank]))

def treatment(names,i:int,j:int,res,mut,nbPages):
    for index in range(i,j):
        name = names[index]
        nbpage = nbPages[name]
        for i in range(1,nbpage+1):
            treat1File(name,i,res,mut)

def treatAllFiles():
    with open("monstList_pro2.json", 'r') as f:
        monstList = json.load(f)
    with open('nbPages.json', 'r') as f:
        nbPages = json.load(f)
    res = set()
    mut = threading.Lock()
    length = len(monstList)
    numberOfThreads = 10
    part = length//numberOfThreads
    for k in range(numberOfThreads):
        i = k*part
        j = (k+1)*part if k!=numberOfThreads-1 else length
        t = threading.Thread(target=treatment, args=(monstList,i,j,res,mut,nbPages))
        t.start()
    for k in range(numberOfThreads):
        t.join()
    res = list(res)
    with open('synth.json', 'w') as f:
        json.dump(res, f, indent=1)

def createID_monst():
    with open('monstList_pro2.json', 'r') as f:
        monstList = json.load(f)
    IDToMonster = {}
    monsterToID = {}
    id = 0
    for name in monstList:
        IDToMonster[id] = name
        monsterToID[name] = id
        id+=1
    with open('IDToMonster.json', 'w') as f:
        json.dump(IDToMonster, f, indent=1)
    with open('monsterToID.json', 'w') as f:
        json.dump(monsterToID, f, indent=1)

def treatment2(synths:list,i:int,j:int,res:dict,mut:threading.Lock,monsterToID:dict):
    for index in range(i,j):
        son = synths[index][0]
        p = []
        for i in range(1,5):
            father = synths[index][i]
            if father != "":
                p.append({"i" : monsterToID[father]})
        synth = synths[index][5]
        rank = synths[index][6]
        tmp = {
            'rt' : rank,
            'st' : synth,
            'p' : p
        }
        id_son = monsterToID[son]
        with mut:
            if id_son not in res:
                res[id_son] = []
            res[id_son].append(tmp)
            
def createDB():
    with open('synth.json', 'r') as f:
        synths = json.load(f)
    with open('monsterToID.json', 'r') as f:
        monsterToID = json.load(f)
    res = {}
    length = len(synths)
    numberOfThreads = 10
    part = length//numberOfThreads
    for k in range(numberOfThreads):
        i = k*part
        j = (k+1)*part if k!=numberOfThreads-1 else length
        t = threading.Thread(target=treatment2, args=(synths,i,j,res,threading.Lock(), monsterToID))
        t.start()
    for k in range(numberOfThreads):
        t.join()
    with open('db.json', 'w') as f:
        json.dump(res, f, indent=1)

createDB()