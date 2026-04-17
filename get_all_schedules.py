import os
import datetime
import pytz
from dotenv import load_dotenv
from si_agenda.client import SIClient
from si_agenda.api import get_events, get_calendars, get_event_details_batch

load_dotenv()

def main():
    login = os.getenv("LOGIN_INT")
    password = os.getenv("PASSWORD_INT")
    
    if not login or not password:
        print("Erreur: identifiants manquants.")
        return

    client = SIClient()
    if not client.login(login, password):
        print("Erreur d'authentification.")
        return
        
    calendars = get_calendars(client)
    if not calendars:
         print("Aucun calendrier trouvé.")
         return
         
    calendar_id = None
    for cal in calendars:
        if cal.id.startswith("USR"):  # Prioritize User calendar
            calendar_id = cal.id
            break
            
    if not calendar_id:
        calendar_id = calendars[0].id

    print(f"Utilisation du calendrier: {calendar_id}")
    
    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(paris_tz)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + datetime.timedelta(days=30)  # Next 30 days
    
    events = get_events(client, calendar_id, start_date.date(), end_date.date())
    
    if events:
        events = get_event_details_batch(client, events, calendar_id, concurrency=10)
        
    # Write to a markdown file for the user to read
    with open("c:/Users/flote/.gemini/antigravity/brain/7eb3a5c5-3f7c-4452-ae9b-a4be0db3b9bf/schedule.md", "w", encoding="utf-8") as f:
        f.write("# Votre Emploi du Temps (30 prochains jours)\n\n")
        if not events:
            f.write("Aucun événement prévu sur cette période.\n")
        else:
            events.sort(key=lambda e: (e.date, e.start_time))
            current_date = None
            for e in events:
                if e.date != current_date:
                    current_date = e.date
                    f.write(f"\n## {current_date}\n")
                    
                room = e.room if e.room else "Non spécifié"
                trainers = ", ".join(e.trainers) if e.trainers else "Non spécifié"
                f.write(f"- **{e.start_time} - {e.end_time}** : {e.name} ({e.type})\n")
                f.write(f"  - 📍 Salle: {room}\n")
                f.write(f"  - 👨‍🏫 Intervenant(s): {trainers}\n")
                
    print(f"Succès, {len(events)} événements récupérés.")

if __name__ == "__main__":
    main()
