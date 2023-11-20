import requests
import bs4
import os
import json
import threading


baseSite:str = 'https://www.woodus.com/den/games/dqm5ds/synth_offspring_results.php?searchfor='

def deduceHeadersfrom(path:str) -> list:
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



if __name__ == '__main__':
    mae()