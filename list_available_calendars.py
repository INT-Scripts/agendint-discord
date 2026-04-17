import os
from dotenv import load_dotenv
from si_agenda.client import SIClient
from si_agenda.api import get_calendars

load_dotenv()

def main():
    login = os.getenv("LOGIN_INT")
    password = os.getenv("PASSWORD_INT")
    
    if not login or not password:
        print("Erreur: identifiants manquants dans le fichier .env.")
        return

    client = SIClient()
    print(f"Tentative de connexion pour {login}...")
    if not client.login(login, password):
        print("Erreur d'authentification.")
        return
    
    print("Récupération des calendriers...")
    calendars = get_calendars(client)
    
    if not calendars:
        print("Aucun calendrier trouvé.")
        return
    
    print("\n=== Emplois du temps disponibles ===")
    for cal in calendars:
        print(f"- {cal.name} (ID: {cal.id})")

if __name__ == "__main__":
    main()
