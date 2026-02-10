import json

Ordner = ".\\Python\\PlexHtmlList\\"

with open(Ordner + "PlexListFilmsElias.json", "r") as f:
    liste1 = json.load(f)

with open(Ordner + "PlexListFilms.json", "r") as f:
    liste2 = json.load(f)
    
for film in liste1:
    if film in liste2:
        print("Gemeinsam", film)