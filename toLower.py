with open('./tmp.json','r') as f:
    tmp = f.read()
    tmp = tmp.lower()
    with open('./tmp_.json','w') as f:
        f.write(tmp)