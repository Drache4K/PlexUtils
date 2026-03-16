import os
import re

def remove_spaces_recursive(path: str) -> None:
    """Entfernt Leerzeichen aus allen Datei- und Ordnernamen rekursiv."""
    
    # Durch alle Einträge im Verzeichnis iterieren
    for name in os.listdir(path):
        old_path = os.path.join(path, name)
        new_name = name.replace(" ", "_")
        new_name = new_name.replace("_-_", "-")
        new_name = new_name.replace("_｜_", "-")
        new_name = re.sub(r'\[[\w_-]+\]', '', new_name)
        new_name = re.sub(r'\.f[0-9]{3}', '', new_name)
        new_name = new_name.replace("_.", ".")
        new_path = os.path.join(path, new_name)
        
        # Wenn der Name Leerzeichen enthält, umbenennen
        if name != new_name:
            os.rename(old_path, new_path)
            print(f"Umbenannt: '{old_path}' -> '{new_path}'")
            old_path = new_path  # Aktualisiere Pfad für rekursiven Aufruf
        
        # Wenn es ein Ordner ist, rekursiv durchgehen
        if os.path.isdir(old_path):
            if "musik" in old_path.lower():
                print(f"Überspringe Musikordner: '{old_path}'")
                continue
            remove_spaces_recursive(old_path)


if __name__ == "__main__":
    # Pfad zum Zielverzeichnis
    target_path = input("Pfad eingeben: ")
    
    if os.path.exists(target_path):
        remove_spaces_recursive(target_path)
        print("Fertig!")
    else:
        print("Pfad existiert nicht!")