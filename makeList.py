from pyquery import PyQuery as pq
import urllib
import json

Ordner = ".\\Python\\PlexHtmlList\\"

html = ""
with open(Ordner + "PlexList.html", "r", encoding="utf-8") as f:
    html = f.read()

d = pq(html)
links = d("[aria-label]")

#print(links)
print("Found", len(links),type(links), "links")
Liste = list(x.attr("aria-label") for x in links.items())
print(Liste)

with open(Ordner + "PlexListFilms.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(Liste, indent=1, ensure_ascii=False))
    