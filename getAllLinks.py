from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# URL die geöffnet werden soll
#url = "https://www.dailymotion.com/search/Die%20W%C3%A4chter%20der%20Tr%C3%A4ume%20Folge%2015/videos"

# Browser-Optionen
options = Options()
# options.add_argument("--headless")  # Auskommentieren um Browser sichtbar zu machen

# Tor-Proxy konfigurieren
options.set_preference('network.proxy.type', 1)
options.set_preference('network.proxy.socks', '127.0.0.1')
options.set_preference('network.proxy.socks_port', 9150)
options.set_preference('network.proxy.socks_remote_dns', True)

# Browser starten
#browser = webdriver.Firefox(options=options)

#profile = webdriver.FirefoxProfile()
#profile.set_preference('network.proxy.type', 1)
#profile.set_preference('network.proxy.socks', '127.0.0.1')
#profile.set_preference('network.proxy.socks_port', 9150)
#browser = webdriver.Firefox(options=options, firefox_profile=profile)
browser = webdriver.Firefox(options=options)


def doUrl(url: str) -> None:
    try:
        # Seite öffnen
        browser.get(url)
        
        # Warten bis die Seite vollständig geladen ist (max 10 Sekunden)
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Zusätzliche Wartezeit für JavaScript-Rendering
        time.sleep(3)
        
        # Seitentitel ausgeben
        print(f"Titel: {browser.title}")
        
        # Gesamten HTML-Quellcode holen
        page_source = browser.page_source
        print(f"\nSeitenlänge: {len(page_source)} Zeichen")
        
        # Alle Links auf der Seite finden
        links = browser.find_elements(By.TAG_NAME, "a")
        print(f"\nAnzahl Links gefunden: {len(links)}")
        
        # Links ausgeben
        
        print("\n--- Gefundene Links ---")
        t = 0
        for link in links:
            href = link.get_attribute("href")
            text = link.text.strip()
            if href and text:
                if t == 1:
                    print(f"{href}")
                    #print(f"{text}")
                    return href
                t =1
        #print("\n--- Spezieller Link ---")
        #print(links[1].get_attribute("href"))
        #return links[1].get_attribute("href")
    except Exception as e:
        print(f"Fehler: {e}")

def getName(url: str) -> str:
    try:
        # Seite öffnen
        browser.get(url)
        
        # Warten bis die Seite vollständig geladen ist (max 10 Sekunden)
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Zusätzliche Wartezeit für JavaScript-Rendering
        time.sleep(3)
        
        # Seitentitel ausgeben
        #print(f"Titel: {browser.title}")
        return browser.title
        
    except Exception as e:
        print(f"Fehler: {e}")

def getLinks(liste: list, retry) -> list:
    global browser, all
    
    notfound = []
    for i in liste:
        print(f"\n--- Seite {i} ---")
        
        tmp = doUrl(f"https://www.dailymotion.com/search/{i}%20Deutsch/videos")
        while tmp == "https://www.dailymotion.com/euronews-de" or type(tmp) != str:
            time.sleep(5)
            tmp = doUrl(f"https://www.dailymotion.com/search/{i}%20Deutsch/videos")
        
        print(type(tmp))
        
        name = getName(tmp)
        print(f"Gefunden: {name}")
        print(f"Gesuche: {i}")
        if not(i.lower() in name.lower()):
            print("Nicht gefunden!")
            if retry:
                x =input("y -> OK, n -> Überspringen, m -> Manuell: ")
                if x.lower() in ["y","j"]:
                    print("OK, weiter...")
                elif x.lower() == "n":
                    print("Überspringen, weiter...")
                    notfound.append(i)
                    continue
                elif x.lower() == "m":
                    tmp = input("Manueller Link: ").strip()
                    print("OK, weiter...")
            else:
                notfound.append(i)
        else:
            print("Gefunden!")
        
            
        all += '"' + tmp + '" '
        all = all.replace('\n','')
        print(all)
    return notfound
    

def serie(name, s,f):
    return [f"{name} Staffel {s} Folge {i}" for i in range(1,f+1)]
if __name__ == "__main__":
    print("=== Dailymotion Link Extraktor ===\n")
    
    filmestr = """
  Tom und Jerry Staffel 5 Folge 8
Tom und Jerry Staffel 5 Folge 9
Tom und Jerry Staffel 5 Folge 15
Tom und Jerry Staffel 5 Folge 16
Tom und Jerry Staffel 5 Folge 20
Tom und Jerry Staffel 5 Folge 22
Tom und Jerry Staffel 5 Folge 23
    """
    
    filmestr = filmestr.strip()
    
    liste = filmestr.split("\n")
    
    print(liste)
    liste = serie("Alf", 4, 24)
    
    all = ""
    
    notfound = getLinks(liste, False)
    
    print("\nNicht gefunden:\n" + str(len(notfound)) + "\n" + "\n".join(notfound))
    
    while len(notfound) > 0 and input("Retry (y/n): ").lower() in ["y","j"]:
        notfound = getLinks(notfound, retry=True)
        print("\nNicht gefunden:\n" + str(len(notfound)) + "\n" + "\n".join(notfound))
    
    browser.quit()
    
    print("\n=== Alle Links ===\n"+ str(len(all.split(' '))-1)+"\n" +all)
    print("\nFertig!")
    
    
    
    #print(all.split(' '))