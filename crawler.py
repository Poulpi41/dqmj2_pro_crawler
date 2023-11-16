import requests
import bs4
import os


baseSite:str = 'https://www.woodus.com/den/games/dqm5ds/synth_offspring_results.php?searchfor='

def deduceHeadersfrom(path:str) -> list[dict,str]:
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
    if not os.path.exists(f'./{monsterName}/'):
        os.makedirs(f'./{monsterName}/')
    for i in range(nbPages):
        if post:
            req = requests.post(url + f'{monsterName}&current={synthsByPage*i}&submitbutton=yes', headers=headers)
        else:
            req = requests.get (url + f'{monsterName}&current={synthsByPage*i}&submitbutton=yes', headers=headers)
        if req.status_code == 200:
            soup = bs4.BeautifulSoup(req.content, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            with open(f'./{monsterName}/synths_{i+1}.html', 'w') as f:
                f.write(table.prettify())
                        
def main():
    headers, get_post = deduceHeadersfrom('headers.txt')
    monsterName = "Wailin'+Weed"
    POST = True if get_post == 'POST' else False
    del headers['Accept-Encoding']
    retrieveAllSynthsFor(headers, baseSite, 27, POST, monsterName)

if __name__ == '__main__':
    main()