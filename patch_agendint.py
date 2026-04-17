import os
import sys
import re

def find_agendint_path():
    # Cherche le dossier agendint dans .venv
    venv_path = os.path.join(os.path.dirname(__file__), ".venv")
    if not os.path.exists(venv_path):
        print("Erreur : le dossier .venv est introuvable. Avez-vous lancé 'uv sync' ?")
        return None
        
    for root, dirs, files in os.walk(venv_path):
        if "agendint" in dirs and "api.py" in os.listdir(os.path.join(root, "agendint")):
            return os.path.join(root, "agendint")
    return None

def patch_client(agendint_dir):
    client_file = os.path.join(agendint_dir, "client.py")
    with open(client_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Si le code est déjà patché, on ignore
    if 'if "ASP.NET_SessionId" not in client.cookies:' in content:
        print("[OK] client.py est déjà patché.")
        return

    # Remplacement pour _finalize_si_login
    old_code = """        async with self.get_client() as client:
            r = await client.get(START_URL, timeout=15.0)
            max_steps = 5
            for _ in range(max_steps):
                if "document.forms[0].submit()" in r.text or "document.formul.submit()" in r.text:
                    r = await self._handle_js_autosubmit(client, r.text, r.url)
                    continue
                break
                
            self.base_url = str(r.url).rsplit("/", 1)[0] + "/"
            bandeau_url = urljoin(self.base_url, "Bandeau.aspx")
            r_bandeau = await client.get(bandeau_url, timeout=15.0)"""

    new_code = """        async with self.get_client() as client:
            if "ASP.NET_SessionId" not in client.cookies:
                r = await client.get(START_URL, timeout=15.0)
                max_steps = 5
                for _ in range(max_steps):
                    if "document.forms[0].submit()" in r.text or "document.formul.submit()" in r.text:
                        r = await self._handle_js_autosubmit(client, r.text, r.url)
                        continue
                    break
                self.base_url = str(r.url).rsplit("/", 1)[0] + "/"
            else:
                self.base_url = "https://si-etudiants.imtbs-tsp.eu/OpDotNet/Noyau/"
                
            bandeau_url = urljoin(self.base_url, "Bandeau.aspx")
            r_bandeau = await client.get(bandeau_url, timeout=15.0)"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        # Il faut aussi ajouter l'enregistrement des cookies si pas déjà fait
        old_cookies = "self.authenticated = True"
        new_cookies = "self.authenticated = True\n                self.cookies = client.cookies"
        if new_cookies not in content:
            content = content.replace(old_cookies, new_cookies)
            
        with open(client_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("[SUCCESS] client.py patché avec succès.")
    else:
        print("[WARNING] Impossible de trouver le bloc à patcher dans client.py.")


def patch_api(agendint_dir):
    api_file = os.path.join(agendint_dir, "api.py")
    with open(api_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Change l'URL LIST_CAL_URL
    if "ListeCal.aspx" in content:
        print("[OK] api.py est déjà patché.")
        return

    old_url = 'LIST_CAL_URL = "https://si-etudiants.imtbs-tsp.eu/Eplug/Agenda/Libre/Calendrier.asp?IdApplication=190&TypeAcces=Utilisateur&IdLien=304"'
    new_url = 'LIST_CAL_URL = "https://si-etudiants.imtbs-tsp.eu/OpDotNet/Eplug/Agenda/Application/ListeCal.aspx"'
    
    # Ajout du `await client.init_agenda_session()` avant le GET des calendriers
    old_get = """    async with client.get_client() as c:
        r = await c.get(LIST_CAL_URL, timeout=10.0)"""
    new_get = """    await client.init_agenda_session()
    async with client.get_client() as c:
        r = await c.get(LIST_CAL_URL, timeout=10.0)"""

    if old_url in content:
        content = content.replace(old_url, new_url)
        content = content.replace(old_get, new_get)
        
        with open(api_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("[SUCCESS] api.py patché avec succès.")
    else:
        print("[WARNING] Impossible de trouver le bloc à patcher dans api.py.")

if __name__ == "__main__":
    print("Recherche de la librairie agendint dans l'environnement virtuel...")
    agendint_path = find_agendint_path()
    if agendint_path:
        print(f"Librairie trouvée à : {agendint_path}")
        patch_client(agendint_path)
        patch_api(agendint_path)
        print("Patch terminé ! Vous pouvez maintenant utiliser uv run.")
    else:
        print("Impossible de patcher : module non trouvé.")
