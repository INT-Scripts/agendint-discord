import os
import datetime
import pytz
import logging
from dotenv import load_dotenv
from si_agenda.client import SIClient
from si_agenda.api import get_events, get_calendars, get_event_details_batch

load_dotenv()

def get_todays_schedules():
    """
    Récupère l'emploi du temps de la journée actuelle pour tous les agendas de type USR
    auxquels l'utilisateur a accès. Retourne un dictionnaire { "Nom": [events...] }.
    """
    login = os.getenv("LOGIN_INT")
    password = os.getenv("PASSWORD_INT")
    
    if not login or not password:
        raise ValueError("LOGIN_INT ou PASSWORD_INT manquant dans le .env")

    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(paris_tz)
    
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)
    today_str = now.strftime("%Y-%m-%d")
    
    client = SIClient()
    if not client.login(login, password):
        raise RuntimeError("Échec de l'authentification à l'intranet.")
    
    calendars = get_calendars(client)
    if not calendars:
        raise ValueError("Aucun calendrier trouvé pour cet utilisateur.")
        
    # Filtrer les calendriers de type USR
    usr_calendars = [cal for cal in calendars if cal.id.startswith('USR')]
    
    if not usr_calendars:
        raise ValueError("Aucun calendrier de type USR trouvé.")
        
    schedules_by_name = {}
    
    for cal in usr_calendars:
        logging.info(f"Récupération pour {cal.name} ({cal.id})...")
        events = get_events(client, cal.id, start_date.date(), end_date.date())
        # Filtre sur le jour précis
        todays_events = [e for e in events if e.date == today_str]
        
        # Hydratation des événements pour obtenir les salles et les intervenants
        if todays_events:
            logging.info(f"Hydratation des détails: {len(todays_events)} évents pour {cal.name}...")
            todays_events = get_event_details_batch(client, todays_events, cal.id, concurrency=5)
            # Tri
            todays_events.sort(key=lambda x: (x.start_time, x.name))

        schedules_by_name[cal.name] = todays_events
        
    return schedules_by_name
