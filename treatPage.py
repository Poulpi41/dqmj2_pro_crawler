import bs4
import json


def formatNameForRequest(name:str) -> str:
    res:str = ""
    res = name.replace(" ", "+")
def getSynthsFrom(path:str) -> list[dict]:
    res:list = []
    with open(path, 'r') as f:
        soup = bs4.BeautifulSoup(f, 'html.parser')
        rows = soup.find_all('tr')[1:]

        for row in rows:
            parents:list = []
            cells = row.find_all('td')
            for i in range(2,9,2):
                if cells[i].text.strip() != "":
                    parents.append(cells[i].text.strip())
            synthtype = cells[9].text.strip()
            ranktype = cells[10].text.strip()
            res.append({"parents": parents, "synthtype": synthtype, "ranktype": ranktype, "numberofparents": len(parents)})
    return res
            
    
def main():
    bigres:list = []
    for i in range(11):
        path:str = f"./Wailin'+Weed/synths_{i+1}.html"
        tmp = getSynthsFrom(path)
        for e in tmp:
            bigres.append(e)

    print (json.dumps(bigres, indent=4))

if __name__ == "__main__":
    main()