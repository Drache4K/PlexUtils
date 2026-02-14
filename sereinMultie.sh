#!/bin/bash

# Anzahl paralleler Downloads (Parameter 2, Standard: 5)
N=${2:-5}
URL=$1

if [ -z "$URL" ]; then
    echo "Usage: $0 <base-url> [parallel-downloads]"
    echo "Example: $0 https://example.com/serie 5"
    exit 1
fi

# Alle alten Downloader-Screens beenden
for s in $(screen -ls | grep "DL_" | awk '{print $1}'); do
    screen -S "$s" -X quit 2>/dev/null
done

Staffel=1
StaffelEnd=0

echo "Starte Downloads mit $N parallelen Screens..."

while [ $StaffelEnd -lt 1 ]; do
    mkdir -p "S$Staffel"
    cd "S$Staffel"
    
    echo "=== Staffel $Staffel ==="
    
    Folge=1
    StopStartingNew=0
    FirstNotFound=-1  # Niedrigste Folge mit 404
    declare -A active_screens  # Screen-Name -> Folgen-Nummer
    declare -A completed_ok    # Erfolgreich heruntergeladene Folgen
    # Arrays explizit leeren (declare -A setzt nicht zurück!)
    active_screens=()
    completed_ok=()
    # Aktuelles Verzeichnis für absolute Pfade
    current_dir="$PWD"
    countDowloaded=0
    
    while true; do
        # Starte neue Downloads bis N erreicht (nur wenn noch nicht gestoppt)
        while [ ${#active_screens[@]} -lt $N ] && [ $StopStartingNew -eq 0 ]; do
            screen_name="DL_S${Staffel}_E${Folge}"
            hardcopy_file="${current_dir}/hardcopy_${Folge}.txt"
            
            echo "Starte Download: Staffel $Staffel, Folge $Folge"
            screen -dmS "$screen_name"
            sleep 0.5
            
            # Download-Befehl mit hardcopy am Ende (absoluter Pfad!)
            screen -S "$screen_name" -X stuff "python ~/voe-dl/dl.py -u \"$URL/staffel-$Staffel/episode-$Folge\" 2>&1; screen -S \"$screen_name\" -X hardcopy \"$hardcopy_file\"; exit\n"
            
            active_screens[$screen_name]=$Folge
            ((Folge++))
            
            # Kurze Pause zwischen Screen-Starts
            sleep 0.3
        done
        
        # Wenn keine aktiven Screens mehr, sind wir fertig mit dieser Staffel
        if [ ${#active_screens[@]} -eq 0 ]; then
            break
        fi
        
        # Warte kurz und prüfe welche Screens fertig sind
        sleep 2
        
        # Sammle beendete Screens (nicht während Iteration löschen!)
        finished_screens=()
        
        # Prüfe jeden aktiven Screen (matcht PID.SCREENNAME Format)
        for screen_name in "${!active_screens[@]}"; do
            if ! screen -ls | grep -q "\.${screen_name}"; then
                # Screen ist beendet
                ep_num=${active_screens[$screen_name]}
                hardcopy_file="${current_dir}/hardcopy_${ep_num}.txt"
                
                if [ -f "$hardcopy_file" ]; then
                    if grep -q "404" "$hardcopy_file"; then
                        echo "Folge $ep_num nicht gefunden (404)"
                        # Merke die niedrigste nicht gefundene Folge
                        if [ $FirstNotFound -eq -1 ] || [ $ep_num -lt $FirstNotFound ]; then
                            FirstNotFound=$ep_num
                        fi
                        # Keine neuen Downloads mehr starten
                        StopStartingNew=1
                    else
                        echo "Folge $ep_num erfolgreich heruntergeladen"
                        completed_ok[$ep_num]=1
                        ((countDowloaded++))
                    fi
                    rm -f "$hardcopy_file"
                else
                    # Keine hardcopy = Download abgestürzt ohne Ergebnis
                    echo "Warnung: Folge $ep_num - keine Rückmeldung (Download abgestürzt?)"
                    # Sicherheitshalber als fehlgeschlagen behandeln
                    if [ $FirstNotFound -eq -1 ] || [ $ep_num -lt $FirstNotFound ]; then
                        FirstNotFound=$ep_num
                    fi
                    StopStartingNew=1
                fi
                finished_screens+=("$screen_name")
            fi
        done
        
        # Entferne beendete Screens nach der Iteration
        for screen_name in "${finished_screens[@]}"; do
            unset active_screens[$screen_name]
        done
    done
    
    cd ..
    
    actual_count=${#completed_ok[@]}
    
    
    # Prüfe ob es die nächste Staffel gibt
    if [ $actual_count -eq 0 ]; then
        # Keine Folge in dieser Staffel gefunden (Folge 1 war schon 404)
        ((StaffelEnd++))
        echo "Keine Folgen in Staffel $Staffel gefunden"
        rmdir "S$Staffel" 2>/dev/null
    else
        StaffelEnd=0
        echo "Staffel $Staffel abgeschlossen mit $actual_count Folgen"
    fi
    
    ((Staffel++))
done

# Aufräumen: Leere Staffel-Ordner entfernen
((Staffel--))
rmdir "S$Staffel" 2>/dev/null

echo "=== Fertig! ==="