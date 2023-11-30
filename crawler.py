from collections import deque
import shutil
from types import FunctionType
from typing import Generator
import requests
import bs4
import os
import json
import threading

def deduceHeadersfrom(path:'str|list') -> list:
    if isinstance(path, str):
        with open(path, 'r') as f:
            headers = {}
            firstLine = f.readline()
            get_post = 'POST' if 'POST' in firstLine else 'GET'
            allButFirst = f.readlines()[1:]
            for line in allButFirst:
                if ': ' in line:
                    key, value = line.split(': ')
                    headers[key] = value.strip()
            return [headers, get_post]
    else:
        return path

def retrieveAllSynthsFor(headers:dict, url:str, nbPages:int, post:bool, monsterName:str):
    synthsByPage = 20
    if not os.path.exists(f'./res/{monsterName}/'):
        os.makedirs(f'./res/{monsterName}/')
    for i in range(nbPages):
        if (os.path.exists(f'./res/{monsterName}/synths_{i+1}.html')):
            continue
        if post:
            req = requests.post(url + f'{monsterName}&current={synthsByPage*i}&submitbutton=yes', headers=headers)
        else:
            req = requests.get (url + f'{monsterName}&current={synthsByPage*i}&submitbutton=yes', headers=headers)
        if req.status_code == 200:
            soup = bs4.BeautifulSoup(req.content, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            with open(f'./res/{monsterName}/synths_{i+1}.html', 'w') as f:
                f.write(table.prettify())

def treatBs4(soup:bs4.BeautifulSoup):
    pages = 1
    div = soup.find('div', {'class': 'c1'})
    allP = div.find_all('p',recursive=False)
    firstP:bs4.BeautifulSoup = allP[0]
    a_s = firstP.find_all('a',recursive=False)
    if len(a_s) > 2:
        pages = len(a_s)-1
    return pages

def retrieves_name():
    baseUrl = 'https://www.woodus.com/den/games/dqm5prods/synth_offspring.php'
    headers, get_post = deduceHeadersfrom('headers.txt')
    monsterNames = []
    POST = True if get_post == 'POST' else False
    del headers['Accept-Encoding']
    if POST:
        req = requests.post(baseUrl, headers=headers)
    else:
        req = requests.get(baseUrl, headers=headers)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.content, 'html.parser')
        select = soup.find('select', {'name': 'searchfor'})
        for option in select.find_all('option'):
            monsterNames.append(option.text.strip().lower())
    else:
        print(f"error: {req.status_code}")
    with open('monsterNames.json', 'w') as f2:
        json.dump(monsterNames,f2, indent=1)


def treatment(monsterNames,i,j,headers,POST,nbPages,url):
    for k in range(i,j):
        monsterName = monsterNames[k]
        # monsterName = 'abyss diver'
        # print (f"treating: {url}{treatNameForRequest(monsterName)}&submitbutton=Envoyer")
        # retrieveAllSynthsFor(headers, baseSite, 27, POST, monsterName)
        if POST:
            req = requests.post(url + treatNameForRequest(monsterName) + '&submitbutton=Envoyer', headers=headers)
        else:
            req = requests.get (url + treatNameForRequest(monsterName) + '&submitbutton=Envoyer', headers=headers)
        if req.status_code == 200:
            # print('succes: '+monsterName)
            soup = bs4.BeautifulSoup(req.content, 'html.parser')
            pages = treatBs4(soup)
            nbPages[1].acquire()
            nbPages[0][monsterName] = pages
            nbPages[1].release()

def treatment2(monsterNames:list,i:int,j:int,headers:dict,POST:bool,nbPages:dict,baseUrl):
    for k in range(i,j):
        monsterName = monsterNames[k]
        retrieveAllSynthsFor(headers, baseUrl, nbPages[0][monsterName], POST, monsterName)

def treatNameForRequest(name:str) -> str:
    return name.replace(' ', '+')

def mae():
    url:str = 'https://www.woodus.com/den/games/dqm5prods/synth_offspring_results.php?searchfor='
    headers, get_post = deduceHeadersfrom('headers.txt')
    POST:bool = True if get_post == 'POST' else False
    del headers['Accept-Encoding']
    with open('monstList_pro2.json', 'r') as f:
        monsterNames:list = json.load(f)
    with open('nbPages.json', 'r') as f:
        nbPages:dict = json.load(f)
    nbPages = (nbPages, threading.Lock())
    length = len(monsterNames)
    threads:list = []
    number_of_threads = 8
    part = length//number_of_threads
    for nb in range(number_of_threads):
        i = nb*part
        j = (nb+1)*part if nb != number_of_threads-1 else length
        t:threading.Thread = threading.Thread(target=treatment2, args=(monsterNames,i,j,headers,POST,nbPages,url))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # with open('nbPages.json', 'w') as f:
    #     json.dump(nbPages[0], f, indent=1)


def makeRequest(url:str, pathToHeaders:'str|dict', monsterName:str,page:int=0,excludeDecrease:bool=True,excludeSame:bool=True,specialOnly:bool=True):
    headers, get_post = deduceHeadersfrom(pathToHeaders)
    POST:bool = True if get_post == 'POST' else False
    if 'Accept-Encoding' in headers:
        del headers['Accept-Encoding']
    requestUrl = url + treatNameForRequest(monsterName) + f'&current={page*20}'
    if excludeDecrease:
        requestUrl += '&excludedecrease=yes'
    if excludeSame:
        requestUrl += '&excludesame=yes'
    if specialOnly:
        requestUrl += '&specialonly=yes'
    requestUrl += '&submitbutton=Submit+Query'
    if POST:
        req = requests.post(requestUrl, headers=headers)
    else:
        req = requests.get (requestUrl, headers=headers)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.content, 'html.parser')
        req.close()
        return soup
    else:
        return None

def makeReq2(url:str, hp:Generator):
    headers,get_post = hp
    POST:bool = True if get_post == 'POST' else False
    if 'Accept-Encoding' in headers:
        del headers['Accept-Encoding']
    if 'Connection' in headers:
        headers['Connection'] = 'close'
    if POST:
        req = requests.post(url, headers=headers)
    else:
        req = requests.get (url, headers=headers)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.content, 'html.parser')
        req.close()
        return soup
    else:
        return None

def extractImageFromTd(td:bs4.BeautifulSoup):
    img = td.find('img')
    if img is None:
        return ""
    return img['src']

corresponding:dict = {
    "son" : 0,
    "father1" : 2,
    "father2" : 4,
    "father3" : 6,
    "father4" : 8,
    "synth": 9,
    "rank" : 10
}
def noResult(soup:bs4.BeautifulSoup):
    if soup is None:
        return True
    table = soup.find('table', {'class': 'sortable'})
    allTr:list = table.find_all('tr')
    return len(allTr) == 1


def findTheLeastResult(nameCoressponding,url , baseMonsterName:str):
    if baseMonsterName in nameCoressponding:
        monsterName = nameCoressponding[baseMonsterName]
    else:
        monsterName = baseMonsterName
    # exclude rank lower , same rank
    # firstReq = makeRequest(url, 'headers.txt', monsterName, 0, True, True, False)
    firstReq = None
    if noResult(firstReq):
        # exclude rank lower
        secondReq = makeRequest(url, 'headers.txt', monsterName, 0, True, False, False)
        if noResult(secondReq):
            # exclude nothing
            thirdReq = makeRequest(url, 'headers.txt', monsterName, 0, False, False, False)
            return thirdReq
        else:
            return secondReq
    else:
        return firstReq

    

def bfs(url:str,entryName:str,datas:dict,monsterVisited:set,lock:threading.Lock = None):
    toVisit:deque = deque() 
    toVisit.append(entryName)
    while len(toVisit) > 0:
        monsterName:str = toVisit.popleft()
        monsterVisited.add(monsterName)
        print(monsterName)
        soup = findTheLeastResult({}, url, monsterName)
        if soup is None:
            continue
        table = soup.find('table', {'class': 'sortable'})
        allTr:list = table.find_all('tr')
        allTr.pop(0)
        if len(allTr) != 0:
            if monsterName not in datas:
                firstRow:bs4.BeautifulSoup = allTr[0]
                firstRowTds = firstRow.find_all('td')
                firstTd = firstRowTds[0]
                firstImg = extractImageFromTd(firstTd)
                if lock is not None:
                    lock.acquire()
                    datas[monsterName] = firstImg
                    lock.release()
                else:
                    datas[monsterName] = firstImg

        for tr in allTr:
            allTd = tr.find_all('td')
            for i in range(corresponding['father1'],corresponding['father4']+1,2):
                fatherTd = allTd[i]
                fatherName = fatherTd.text.strip().lower()
                if fatherName == "":
                    break
                if fatherName not in monsterVisited:
                    toVisit.append(fatherName)
                    monsterVisited.add(fatherName)
                
            
    

def crawlList(initialElement = "abyss diver"):
    url:str = 'https://www.woodus.com/den/games/dqm5prods/synth_offspring_results.php?searchfor='
    monsterDiscovered = set()
    datas:dict = {}
    bfs(url,initialElement, datas, monsterDiscovered)
    monsterList:list = list(monsterDiscovered)
    monsterList.sort()
    with open('monsterList.json', 'w') as f:
        json.dump(monsterList, f, indent=1)
    with open('monsterListWithImg.json', 'w') as f:
        json.dump(datas, f, indent=1)
    
def paraCrawlList(initialElements = "abyss diver"):
    url:str = 'https://www.woodus.com/den/games/dqm5prods/synth_offspring_results.php?searchfor='
    monsterDiscovered = set()
    datas:dict = {}
    lock:threading.Lock = threading.Lock()
    threads:list = []
    nthreads = 8
    for i in range(nthreads):
        t:threading.Thread = threading.Thread(target=bfs, args=(url,initialElements[i], datas, monsterDiscovered,lock))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    monsterList:list = list(monsterDiscovered)
    monsterList.sort()
    with open('monsterList.json', 'w') as f:
        json.dump(monsterList, f, indent=1)
    with open('monsterListWithImg.json', 'w') as f:
        json.dump(datas, f, indent=1)

def difBetweenTwoMonstList(path1:str, path2:str, path3:str):
    res:list = []
    with open(path1, 'r') as f:
        list1:list = json.load(f)
    with open(path2, 'r') as f:
        list2:list = json.load(f)
    with open(path3, 'r') as f:
        nameCoressponding:dict = json.load(f)
    for name in list1:
        if name not in list2:
            if name not in nameCoressponding:
                res.append(name)
    return res
def addSpecials(discovered:set, datas:dict):
    urlSpecialSynths:str = 'https://www.woodus.com/den/games/dqm5prods/specialsynthonly.php'
    headers, get_post = deduceHeadersfrom('headers.txt')
    POST:bool = True if get_post == 'POST' else False
    del headers['Accept-Encoding']
    if POST:
        req = requests.post(urlSpecialSynths, headers=headers)
    else:
        req = requests.get (urlSpecialSynths, headers=headers)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.content, 'html.parser')
        table = soup.find('table', {'class': 'sortable'})
        allTr:list = table.find_all('tr')
        allTr.pop(0)
        for tr in allTr:
            allTd = tr.find_all('td')
            for i in range(corresponding['father1'],corresponding['father4']+1,2):
                fatherTd = allTd[i]
                fatherName = fatherTd.text.strip().lower()
                if fatherName == "":
                    break
                if fatherName not in discovered:
                    discovered.add(fatherName)
                    datas[fatherName] = extractImageFromTd(allTd[corresponding['son']])
            sonName = allTd[corresponding['son']].text.strip().lower()
            sonImage = extractImageFromTd(allTd[corresponding['son']])
            if sonName not in discovered:
                discovered.add(sonName)
                datas[sonName] = sonImage
        with open('new_monsterListWithImg.json', 'w') as f:
            json.dump(datas, f, indent=1)
        with open('new_monsterList.json', 'w') as f:
            json.dump(list(discovered), f, indent=1)
    
def treatNameForImage(monsterName:str):
    return monsterName.replace(' ', '_').replace("'",'')
    
def tryImage(monsterName:str):
    return f"https://www.woodus.com/den/gallery/graphics/dqm5prods/monstericons/{treatNameForImage(monsterName)}.webp"
def downloadImage(url:str,path:str):
    headers, get_post = deduceHeadersfrom('headers.txt')
    # del headers['Accept-Encoding']
    req = requests.get(url, stream=True, headers=headers)
    if req.status_code == 200:
        with open(path, 'wb') as f:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, f)
    return req.status_code

def treatment3(monstList:list, i:int, j:int,nameCoressponding:dict,alreadyDownloaded:list):
    for k in range(i,j):
        monsterName = monstList[k]
        if monsterName in alreadyDownloaded:
            continue
        if monsterName in nameCoressponding:
            tmp = nameCoressponding[monsterName]
            if tmp in alreadyDownloaded:
                continue
        url = tryImage(monsterName)
        path = f"./images/icons/{monsterName}.webp"
        status:int = downloadImage(url, path)
        if status != 200:
            if monsterName in nameCoressponding:
                monsterName = nameCoressponding[monsterName]
                url = tryImage(monsterName)
                path = f"./images/icons/{monsterName}.webp"
                status:int = downloadImage(url, path)
                if status != 200:
                    print(f"error: {status} for {monsterName}")
            else:
                print(f"error: {status} for {monsterName}")

def treatment4(i:int,j:int,list1:list, list2:list, nameCoressponding:dict,res:list):
    for k in range(i,j):
        name = list1[k]
        if name not in list2:
            if name not in nameCoressponding or nameCoressponding[name] not in list2:
                res.append(name)

def treatment5(name:str,res:list,h:Generator,lock:threading.Lock=None):
    soup = makeRequest('https://www.woodus.com/den/games/dqm5prods/synth_offspring_results.php?searchfor=', h, name, 0, False, False, False)
    if soup is not None:
        if lock is not None:
            lock.acquire()
            res.append({'n':name,'s':soup})
            lock.release()
        else:
            res.append({'n':name,'s':soup})
def treatment5bis(i:int,j:int,ml:list,res:list,h:Generator):
    for k in range(i,j):
        name = ml[k]
        print(name)
        soup = makeRequest('https://www.woodus.com/den/games/dqm5prods/synth_offspring_results.php?searchfor=', h, name, 0, False, False, False)
        if soup is not None:
            res.append({'n':name,'s':soup})

def test(url):
    req = requests.get(url)
    if req.status_code == 200:
        return True
    else:
        return False
    

def treatment6(i:int,j:int,res:list,pages:dict,mut:threading.Lock):
    for k in range(i,j):
        name,soup = res[k]['n'],res[k]['s']
        with mut:
            pages[name] = treatBs4(soup)

def treatment7(i:int,j:int,datas:list,revUrl:dict,mut:threading.Lock,res:dict,hp:Generator):
    # count = 1
    for k in range(i,j):
        url = datas[k]
        print(url)
        soup = makeReq2(url, hp)
        name = revUrl[url]
        if name not in res:
            with mut:
                res[name] = []
        if soup is None:
            continue
        table = soup.find('table', {'class': 'sortable'})
        if table is not None:
            with mut:
                res[name].append({'html':str(table),'url':url})
        # if count%20 == 0:
        #     print(f"treated: {count}")
        # count += 1
    

def executeInParallel(nbThreads:int, totalSizeToDispatch:int,routine:FunctionType,kwarg:dict,begEnd:list=[]):
    """distribute to each thread a part of the work and execute the routine

    Args:
        nbThreads (int): the desired number of threads
        totalSizeToDispatch (int): the total size of the work to distribute
        routine (FunctionType): the function to execute in parallel, must have a 'i' and 'j' parameter which are respectively the start and end of the part of the work 
        kwarg (dict): additional argument of the routine
    """
    threads:list = []
    if len(begEnd) == 2:
        totalSizeToDispatch = begEnd[1]-begEnd[0]

    part = totalSizeToDispatch//nbThreads

    for k in range(nbThreads):
        i = k*part
        if len(begEnd) == 2:
            i += begEnd[0]
        j = (k+1)*part if k != nbThreads-1 else totalSizeToDispatch
        t:threading.Thread = threading.Thread(target=routine, kwargs={**kwarg, 'i':i, 'j':j})
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

def executeInParallel2(nbThreads:int,routine:FunctionType,kwargs:dict):
    """execute the routine in parallel

    Args:
        nbThreads (int): the desired number of threads
        routine (FunctionType): the function to execute in parallel
        kwargs (dict): arguments of the routine
    """
    threads:list = []
    monsterList:list = kwargs['ml']
    del kwargs['ml']
    for k in range(nbThreads):
        kwargs['name'] = monsterList[k]
        t:threading.Thread = threading.Thread(target=routine, kwargs=kwargs)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

INIT = 0
PROC = 2
PROC_TOTAL = 3


if __name__ == '__main__':
    with open('urlList.json', 'r') as f:
        urlList:list = json.load(f)
    with open('reverseUrl.json', 'r') as f:
        reverseUrl:dict = json.load(f)
        
    res:dict = {}
    length = len(urlList)//PROC_TOTAL
    # length = 1
    executeInParallel(80,length,treatment7,{'datas':urlList,'revUrl':reverseUrl,'mut':threading.Lock(),'res':res,'hp':deduceHeadersfrom('headers.txt')},[INIT,2*length])
    with open('res.json', 'w') as f:
        json.dump(res, f, indent=1)
    