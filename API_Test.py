from plexapi.server import PlexServer
import dotenv
import os
import json

env = dotenv.find_dotenv()
dotenv.load_dotenv()
print(env)

if "plexutils" in env.lower():
   ip = os.getenv("IP")
   token = os.getenv("TOKEN")

print("ip: "+ip)
print("token: "+token)


try:
    baseurl = f"http://{ip}:32400"
    #token = token
    plex = PlexServer(baseurl, token)
except:
    print("Nö")
    baseurl = 'http://localhost:32400'
    #token = token
    plex = PlexServer(baseurl, token)

    

#print(plex.library)

movies = plex.library.section('Filme')
Liste = []
for video in movies.search():
    print(video.title)
    Liste.append(video.title)


Ordner = env.replace(".env","")

user = os.getlogin()

with open(Ordner + f"PlexListFilms_{user}.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(Liste, indent=2, ensure_ascii=False))