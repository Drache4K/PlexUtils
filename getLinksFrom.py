import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_website_content_static(url):
    """
    Lädt den HTML-Inhalt einer Website (statisch)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Laden der Website: {e}")
        return None

def get_website_content_dynamic(url, wait_time=10):
    """
    Lädt eine Website mit Selenium (JavaScript-basiert)
    und wartet auf das Laden der Streams
    """
    driver = None
    try:
        print("Starte Browser...")
        
        # Chrome-Optionen
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        # options.add_argument('--headless')  # Kommentieren Sie aus, um Browser zu sehen
        
        # WebDriver initialisieren
        print("Installiere ChromeDriver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        print(f"Lade Website: {url}")
        driver.get(url)
        
        # Warte bis Videos/Streams geladen sind
        print(f"Warte {wait_time} Sekunden auf Stream-Laden...")
        time.sleep(wait_time)
        
        # Alternative: Warte auf ein spezifisches Element
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
            )
            print("✓ Video-Element gefunden!")
        except:
            print("ℹ Kein Video-Element gefunden, fahre fort...")
        
        # HTML abrufen
        html = driver.page_source
        print(f"✓ HTML geladen ({len(html)} Zeichen)")
        
        # Netzwerk-Traffic abfangen (M3U8 Requests)
        print("\nSuche nach M3U8-Streams in Netzwerk-Logs...")
        
        # Methode: window.performance nutzen
        try:
            resources = driver.execute_script("""
                return window.performance.getEntriesByType('resource')
                    .filter(r => r.name.includes('m3u8'))
                    .map(r => r.name);
            """)
            
            if resources:
                print(f"✓ {len(resources)} M3U8 in Performance-Logs gefunden!")
            else:
                print("ℹ Keine M3U8 in Performance-Logs gefunden")
                
            driver.quit()
            return html, resources
        except Exception as e:
            print(f"⚠ Performance-Abfrage fehlgeschlagen: {e}")
            driver.quit()
            return html, []
            
    except Exception as e:
        print(f"✗ Fehler beim Laden mit Browser: {e}")
        print(f"  Fehlertyp: {type(e).__name__}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None, []

def extract_m3_streams(html_content, base_url="", network_streams=None):
    """
    Filtert M3U/M3 Video-Streams aus HTML und Netzwerk-Logs heraus
    """
    if network_streams is None:
        network_streams = []
    
    streams = []
    
    # Streams von Netzwerk-Traffic
    for stream in network_streams:
        if stream not in streams:
            streams.append(stream)
    
    # Pattern 1: M3U Links in href Attributen
    m3u_pattern = r'href=["\'](.*?\.m3u8?[^"\']*)["\']'
    m3u_links = re.findall(m3u_pattern, html_content, re.IGNORECASE)
    
    for link in m3u_links:
        absolute_url = urllib.parse.urljoin(base_url, link)
        if absolute_url not in streams:
            streams.append(absolute_url)
    
    # Pattern 2: M3U Links im Quellcode (URLs)
    streaming_pattern = r'(https?://[^\s"\'<>]*\.m3u8?[^\s"\'<>]*)'
    streaming_links = re.findall(streaming_pattern, html_content)
    
    for link in streaming_links:
        if link not in streams:
            streams.append(link)
    
    # Pattern 3: Video src Attribute
    video_src_pattern = r'<video[^>]*src=["\'](.*?)["\']'
    video_srcs = re.findall(video_src_pattern, html_content, re.IGNORECASE)
    
    for link in video_srcs:
        if ".m3u" in link.lower():
            absolute_url = urllib.parse.urljoin(base_url, link)
            if absolute_url not in streams:
                streams.append(absolute_url)
    
    # Pattern 4: HLS/Stream URLs in JSON/JS
    hls_pattern = r'["\'](?:url|src|stream|path)["\']?\s*[:=]\s*["\']?(https?://[^\s"\'<>]*\.m3u8?[^\s"\'<>]*)'
    hls_matches = re.findall(hls_pattern, html_content, re.IGNORECASE)
    
    for link in hls_matches:
        if link not in streams:
            streams.append(link)
    
    return streams

def extract_all_links(html_content):
    """
    Extrahiert alle Links und findet Video-stream-relevante
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    all_links = {
        'streams': [],
        'videos': [],
        'playlists': []
    }
    
    # Alle Links sammeln
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        if '.m3u' in href.lower():
            all_links['streams'].append(href)
        elif any(ext in href.lower() for ext in ['.mp4', '.ts', '.m4s']):
            all_links['videos'].append(href)
        elif any(ext in href.lower() for ext in ['.m3u', '.pls', '.playlist']):
            all_links['playlists'].append(href)
    
    return all_links

def display_streams(streams):
    """
    Zeigt gefundene Streams formatiert an
    """
    if not streams:
        print("Keine Streams gefunden!")
        return
    
    print(f"\n{'='*60}")
    print(f"Gefundene M3 Video-Streams ({len(streams)}):")
    print(f"{'='*60}\n")
    
    for i, stream in enumerate(streams, 1):
        print(f"{i}. {stream}\n")

def main():
    # URLs zum Testen (anpassen!)
    url = input("Gib die Website-URL ein: ").strip()
    
    if not url:
        print("✗ Keine URL eingegeben!")
        return
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    print(f"\nVerarbeite: {url}\n")
    
    # Wähle Lade-Methode
    print("Wähle Lade-Methode:")
    print("1. Statisch (schnell, nur HTML)")
    print("2. Dynamisch (mit Browser, JavaScript-basierte Streams)")
    
    method = input("\nEingabe (1 oder 2): ").strip()
    
    if method not in ["1", "2"]:
        print("✗ Ungültige Eingabe!")
        return
    
    print("\n" + "="*60)
    
    html = None
    network_streams = []
    
    if method == "2":
        # Dynamisch mit Selenium
        wait_time_input = input("Sekunden warten auf Streams (Standard: 10): ").strip()
        wait_time = int(wait_time_input) if wait_time_input.isdigit() else 10
        
        print()
        html, network_streams = get_website_content_dynamic(url, wait_time)
        
        if network_streams:
            print(f"✓ {len(network_streams)} Streams in Netzwerk-Traffic gefunden!")
        
        if html is None:
            print("\n✗ Browser konnte Website nicht laden!")
            print("  Bitte überprüfe:")
            print("  - Ist die URL korrekt?")
            print("  - Ist die Website erreichbar?")
            print("  - Benötigst du ein VPN?")
            return
    else:
        # Statisch
        print(f"Lade Website: {url}\n")
        html = get_website_content_static(url)
        
        if html is None:
            print("\n✗ Website konnte nicht geladen werden!")
            print("  Bitte überprüfe:")
            print("  - Ist die URL korrekt?")
            print("  - Ist die Website erreichbar?")
            print("  - Liegt ein Netzwerkfehler vor?")
            print("\n  Tipp: Versuche die dynamische Methode (Option 2)")
            return
    
    if html:
        print("\n✓ Website erfolgreich geladen!")
        
        # M3 Streams extrahieren
        streams = extract_m3_streams(html, url, network_streams)
        
        # Zusätzliche Links extrahieren
        links = extract_all_links(html)
        
        # Ergebnisse anzeigen
        display_streams(streams)
        
        # Optional: Weitere Links anzeigen
        if links['videos']:
            print(f"\n📹 Video-Dateien gefunden: {len(links['videos'])}")
            for video in links['videos'][:5]:
                print(f"  - {video}")
        
        # Ergebnisse speichern
        save_option = input("\nErgebnisse speichern? (j/n): ").lower()
        if save_option == 'j':
            filename = input("Dateiname (Standard: extracted_streams.txt): ").strip()
            if not filename:
                filename = "extracted_streams.txt"
            
            return
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Streams von: {url}\n")
                    f.write(f"Lade-Methode: {'Dynamisch (Selenium)' if method == '2' else 'Statisch'}\n")
                    f.write("="*60 + "\n\n")
                    for stream in streams:
                        f.write(stream + "\n")
                print(f"✓ Gespeichert in '{filename}'")
            except Exception as e:
                print(f"✗ Fehler beim Speichern: {e}")

if __name__ == "__main__":
    main()
