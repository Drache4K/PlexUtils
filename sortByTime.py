import os
import re
from pathlib import Path


def get_creation_time(file_path: Path) -> float:
    """Gibt die Erstellungszeit einer Datei zurück."""
    stat = file_path.stat()
    # Unter Windows: st_ctime ist die Erstellungszeit
    # Unter Linux: st_ctime ist die letzte Metadatenänderung
    return stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime

def cutName(name: str) -> str:
    return re.sub(r'\_e[0-9]{2,3}', '', name).replace('？', '').replace('：', '').replace('｜','').replace('…','').replace('...', '').replace('__temp__', '')


def sort_and_rename_files(folder_path: str, prefix: str = "Folge", dry_run: bool = True):
    """
    Sortiert alle Dateien in einem Ordner nach Erstellungszeit 
    und benennt sie mit fortlaufender Nummerierung um.
    
    Args:
        folder_path: Pfad zum Ordner mit den Dateien
        prefix: Präfix für die neuen Dateinamen (z.B. "Folge")
        dry_run: Wenn True, werden Änderungen nur angezeigt, nicht durchgeführt
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Fehler: Ordner '{folder_path}' existiert nicht!")
        return
    
    print(f"Ordner: {folder.resolve()}\n")
    # Alle Dateien im Ordner sammeln (keine Unterordner)
    #files = folder.iterdir()
    #print("Get 2 Files")
    files = [f for f in folder.iterdir() if f.is_file()]
    
    if not files:
        print("Keine Dateien im Ordner gefunden!")
        return
    
    print("Sort")
    # Nach Erstellungszeit sortieren (älteste zuerst)
    files.sort(key=get_creation_time)  # Zuerst alphabetisch sortieren für Konsistenz
    #files_sorted = sorted(files, key=get_creation_time)
    
    print(f"Gefundene Dateien: {len(files)}")
    print("-" * 60)
    
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv'}
    thumbnail_extensions = {'.webp', '.jpg', '.jpeg', '.png', '.gif'}

    videos = []
    thumbnails = []

    for i in files:
        if i.suffix in video_extensions:
            videos.append(i)
        elif i.suffix in thumbnail_extensions:
            thumbnails.append(i)


    pairs = []
    print(len(files))

    for i in videos:
        
        vid = cutName(i.stem)
        #print(f"\nLooking for match for video: {vid}")
        for build in thumbnails:
            bild = cutName(build.stem)
            #print(vid)
            #print(bild)
            #print(f"  {vid==bild}")
            if vid == bild:
                pairs.append((i, build))
                thumbnails.remove(build)
                break
        else:
            pairs.append((i, None))
    
    #for x,y in pairs:
    #    files.remove(x)
    #    files.remove(y)

    #print(len(files))
    '''
    for i in files:
        if i.suffix == '.mp4':
            vid = cutName(i.stem)
            print(f"\nLooking for match for video: {vid}")
            for build in files:
                if build.suffix == '.webp':
                    bild = cutName(build.stem)
                    print(vid)
                    print(bild)
                    print(f"  {vid==bild}")
                    if vid == bild:
                        #pairs.append((i, build))
                        #files.remove(build)
                        #files.remove(i)
                        break'''

    # Umbenennungen planen
    renames = []
    '''
    for index, file in enumerate(files, start=1):
        extension = file.suffix
        new_name = f"{cutName(file.stem)}_e{index:02d}{extension}"
        new_path = folder / new_name
        renames.append((file, new_path))
        
        # Erstellungszeit anzeigen
        from datetime import datetime
        creation_time = datetime.fromtimestamp(get_creation_time(file))
        print(f"{index:3}. [{creation_time}] {file.name}")
        print(f"      -> {new_name}")'''
    
    for index, (vid_file, img_file) in enumerate(pairs, start=1):
        extension_vid = vid_file.suffix
        
        new_name_vid = cutName(vid_file.stem) + f"_e{index:02d}"
        #new_name_img = f"{re.sub(r'\_e[0-9]{2,3}', '', img_file.stem).replace('？', '').replace('：', '').replace('｜','').replace('…','').replace('...', '').replace('__temp__', '')}_e{index:02d}{}"
        new_path_vid = folder / (new_name_vid + extension_vid)
        renames.append((vid_file, new_path_vid))

        if img_file != None:
            extension_img = img_file.suffix
            new_path_img = folder / (new_name_vid + extension_img)
            renames.append((img_file, new_path_img))
        
        # Erstellungszeit anzeigen
        from datetime import datetime
        creation_time = datetime.fromtimestamp(get_creation_time(vid_file))
        if img_file == None:
            print(f"{index:3}. [{creation_time}] {vid_file.name}")
            print(f"      -> {new_path_vid}")
        else:
            print(f"{index:3}. [{creation_time}] {vid_file.name} + {img_file.name}")
            print(f"      -> {new_name_vid}{extension_vid} + {new_name_vid}{extension_img}")

    print("-" * 60)
    
    if dry_run:
        print("\n⚠️  DRY RUN - Keine Änderungen durchgeführt!")
        print("Setze dry_run=False um die Dateien umzubenennen.")
        return
    
    # Prüfe ob es Überschneidungen gibt
    old_names = {r[0].name for r in renames}
    new_names = {r[1].name for r in renames}
    has_conflicts = bool(old_names & new_names)  # Schnittmenge
    
    print("\nBenennung wird durchgeführt...")
    
    if has_conflicts:
        # Mit temporären Namen um Konflikte zu vermeiden
        print("(Konflikte erkannt - nutze temporäre Namen)")
        temp_renames = []
        for old_path, new_path in renames:
            temp_path = folder / f"__temp__{old_path.name}"
            os.rename(old_path, temp_path)
            temp_renames.append((temp_path, new_path))
        
        for temp_path, new_path in temp_renames:
            os.rename(temp_path, new_path)
            print(f"✓ {new_path.name}")
    else:
        # Direkt umbenennen - keine Konflikte möglich
        for old_path, new_path in renames:
            os.rename(old_path, new_path)
            print(f"✓ {new_path.name}")
    
    print(f"\n✅ {len(renames)} Dateien erfolgreich umbenannt!")


if __name__ == "__main__":
    # ===== KONFIGURATION =====
    
    # Ordnerpfad mit den Dateien
    FOLDER = input("Ordnerpfad eingeben: ")  # <- HIER ANPASSEN!
    
    # Präfix für die neuen Dateinamen
    PREFIX = "Folge"  # Ergebnis: Folge_01.mp4, Folge_02.mp4, ...
    
    # Sicherheitsmodus: True = nur Vorschau, False = wirklich umbenennen
    DRY_RUN = True
    
    # ==========================
    print("Go")
    sort_and_rename_files(FOLDER, PREFIX, DRY_RUN)


    go = input("Change? (y/n): ")
    if go.lower() == 'y':
        DRY_RUN = False
        sort_and_rename_files(FOLDER, PREFIX, DRY_RUN)
