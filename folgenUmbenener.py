import os
import re


def extract_episode_info(filename: str):
    """Extrahiert Serienname und Folgennummer aus dem Dateinamen."""
    
    # Entferne Dateiendung für die Analyse
    name_without_ext = os.path.splitext(filename)[0]
    
    # Entferne YouTube-ID in eckigen Klammern [abc123...]
    name_clean = re.sub(r'\[[\w_-]+\]', '', name_without_ext)
    
    # Entferne unnötige Teile
    remove_patterns = [
        r'_?-?_?HD_?',
        r'_?-?_?ALLE_Folgen_?',
        r'_?-?_?ALLE_Staffeln_?',
        r'_?-?_?KIKA_?',
        r'_?-?_?deutsche_?',
    ]
    for pattern in remove_patterns:
        name_clean = re.sub(pattern, '', name_clean, flags=re.IGNORECASE)
    
    # Versuche Folgennummer zu finden (verschiedene Formate)
    # Format: "Folge_11", "Folge 11", "Folge_011", "Episode_5", "E05", etc.
    episode_patterns = [
        r'[Ff]olge[_\s]*(\d+)',
        r'[Ee]p[_\s]*(\d+)',
        r'[Ee]pisode[_\s]*(\d+)',
        r'[Ee](\d+)',
        r'(\d+).',
        r'[_\s](\d+)[_\s]*[-_]',  # Nummer zwischen Trennzeichen
    ]
    
    #print(name_clean)

    episode_num = None
    for pattern in episode_patterns:
        match = re.search(pattern, name_clean)
        if match:
            episode_num = int(match.group(1))
            break
    

    # Versuche Serienname zu extrahieren (alles vor "Folge" oder "Episode")
    series_name = None
    series_match = re.match(r'^([A-Za-zÄÖÜäöüß]+)', name_clean)
    if series_match:
        series_name = series_match.group(1)
    
    return series_name, episode_num


def extract_season_from_folder(folder_name: str):
    """Extrahiert Staffelnummer aus Ordnernamen wie 'Staffel 1', 'Season 2', 'S01'."""
    patterns = [
        r'[Ss]taffel[_\s]*(\d+)',
        r'[Ss]eason[_\s]*(\d+)',
        r'[Ss](\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, folder_name)
        if match:
            return int(match.group(1))
    return None


def extract_series_from_folder(folder_name: str) -> str:
    """Bereinigt Ordnernamen für Seriennamen."""
    # Entferne Staffel-Infos aus dem Namen
    clean_name = re.sub(r'[_\s]*[Ss]taffel[_\s]*\d+', '', folder_name)
    clean_name = re.sub(r'[_\s]*[Ss]eason[_\s]*\d+', '', clean_name)
    clean_name = re.sub(r'[_\s]*[Ss]\d+', '', clean_name)
    # Ersetze Unterstriche durch Leerzeichen
    #clean_name = clean_name.replace('_', ' ').strip()
    return clean_name if clean_name else folder_name


def generate_plex_name(series_name: str, season: int, episode: int, extension: str) -> str:
    """Generiert einen Plex-kompatiblen Dateinamen."""
    # Format: "Serienname - S01E01.ext"
    return f"{series_name}-s{season:02d}e{episode:02d}{extension}"


def rename_for_plex(path: str, series_name: str = None, season: int = 1, dry_run: bool = True) -> int:
    """Benennt alle Videodateien im Ordner für Plex um. Gibt Anzahl der Dateien zurück."""
    
    video_extensions = {'.mp4', '.mkv', '.avi', '.webm', '.mov', '.m4v'}
    count = 0
    
    files = sorted(os.listdir(path))
    
    for filename in files:
        filepath = os.path.join(path, filename)
        
        # Nur Dateien, keine Ordner
        if not os.path.isfile(filepath):
            continue
        
        # Nur Videodateien
        _, ext = os.path.splitext(filename)
        if ext.lower() not in video_extensions:
            continue
        
        if filename.lower().startswith("."):
            #print(f"  ⚠️  Ignoriere versteckte Datei: {filename}")
            continue

        # Extrahiere Info aus Dateiname
        detected_series, episode_num = extract_episode_info(filename)
        
        if episode_num is None:
            print(f"  ⚠️  Keine Folgennummer gefunden: {filename}")
            continue
        
        # Verwende übergebenen Seriennamen oder erkannten
        final_series = series_name or detected_series or "Unbekannt"
        
        # Generiere neuen Namen
        new_name = generate_plex_name(final_series, season, episode_num, ext)
        new_path = os.path.join(path, new_name)
        
        if dry_run:
            if os.path.exists(new_path):
                #print(f"  ⚠️  Existiert bereits: {new_name}")
                pass
            else:
                print(f"  🔍 {filename}\n     → {new_name}")
        else:
            if os.path.exists(new_path):
                print(f"  ⚠️  Existiert bereits: {new_name}")
                continue
            os.rename(filepath, new_path)
            print(f"  ✅ {filename}\n     → {new_name}")
        count += 1
    
    return count

def process_SingelSeries_folder(series_path: str, dry_run: bool = True) -> int:
    total_count = 0
        
    if not os.path.isdir(series_path):
        return 0
    
    # Prüfe ob es Staffel-Unterordner gibt
    has_season_folders = False
    for sub_entry in os.listdir(series_path):
        sub_path = os.path.join(series_path, sub_entry)
        if os.path.isdir(sub_path) and extract_season_from_folder(sub_entry):
            has_season_folders = True
            break

    series_name = extract_series_from_folder(os.path.basename(series_path))
    
    if has_season_folders:
        # Struktur: Serie/Staffel X/Dateien
        for season_folder in sorted(os.listdir(series_path)):
            season_path = os.path.join(series_path, season_folder)
            
            if not os.path.isdir(season_path):
                continue
            
            season_num = extract_season_from_folder(season_folder)
            if season_num is None:
                season_num = 1
            
            print(f"\n📁 {series_name} - Staffel {season_num}")
            print(f"   ({season_path})")
            count = rename_for_plex(season_path, series_name, season_num, dry_run)
            total_count += count
    else:
        # Struktur: Serie/Dateien (keine Staffel-Unterordner)
        print(f"\n📁 {series_name} - Staffel 1")
        print(f"   ({series_path})")
        count = rename_for_plex(series_path, series_name, season=1, dry_run=dry_run)
        total_count += count
    
    return total_count
    

def rename_recursive(root_path: str, dry_run: bool = True) -> None:
    """Geht rekursiv durch alle Serienordner und benennt Dateien um.
    
    Erwartet Struktur wie:
    - root_path/Serienname/Staffel 1/Folge_1.mp4
    - root_path/Serienname/Folge_1.mp4 (Staffel 1 angenommen)
    """
    
    total_count = 0
    
    for entry in sorted(os.listdir(root_path)):
        series_path = os.path.join(root_path, entry)
        print(f"{series_path} ---")
        if os.path.exists(os.path.join(series_path, ".ignore")):
            print(f"  ⚠️  Ignoriere Ordner: {series_path}")
            continue
        total_count += process_SingelSeries_folder(series_path, dry_run)
    
    print(f"\n{'='*50}")
    print(f"Gesamt: {total_count} Dateien {'gefunden' if dry_run else 'umbenannt'}")


if __name__ == "__main__":
    print("=== Plex Datei-Umbenenner ===\n")
    
    print("Modi:")
    print("  1. Einzelner Ordner")
    print("  2. Rekursiv (Serienordner mit Staffeln)")
    mode = input("\nModus wählen (1/2 All Series/3 One Series): ").strip()
    
    target_path = input("Pfad: ").strip()
    
    if not os.path.exists(target_path):
        print("Pfad existiert nicht!")
        exit(1)
    
    if mode == "3":
        # Rekursiver Modus
        print("\n--- Vorschau (Dry Run) ---")
        process_SingelSeries_folder(target_path, dry_run=True)
        
        confirm = input("\nUmbenennung durchführen? (j/n): ").strip().lower()
        if confirm in ['j','y']:
            print("\n--- Umbenennung ---")
            process_SingelSeries_folder(target_path, dry_run=False)
            print("\nFertig!")
        else:
            print("Abgebrochen.")

    elif mode == "2":
        # Rekursiver Modus
        print("\n--- Vorschau (Dry Run) ---")
        rename_recursive(target_path, dry_run=True)
        
        confirm = input("\nUmbenennung durchführen? (j/n): ").strip().lower()
        if confirm in ['j','y']:
            print("\n--- Umbenennung ---")
            rename_recursive(target_path, dry_run=False)
            print("\nFertig!")
        else:
            print("Abgebrochen.")
    elif mode == "1":
        # Einzelordner-Modus
        series_input = input("Serienname (Enter für automatische Erkennung): ").strip()
        series_name = series_input if series_input else None
        
        season_input = input("Staffelnummer (Standard: 1): ").strip()
        season = int(season_input) if season_input else 1
        
        print("\n--- Vorschau (Dry Run) ---\n")
        rename_for_plex(target_path, series_name, season, dry_run=True)
        
        confirm = input("\nUmbenennung durchführen? (j/n): ").strip().lower()
        if confirm in ['j','y']:
            print("\n--- Umbenennung ---\n")
            rename_for_plex(target_path, series_name, season, dry_run=False)
        print("Fertig!")
    else:
        print("Abgebrochen.")