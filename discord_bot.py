import os
import requests
import datetime
import pytz
import logging
import traceback
import json

def get_webhook_url():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL manquant dans le .env")
    return webhook_url

def send_error_to_discord(exception):
    try:
        url = get_webhook_url()
        error_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        # Tronquer si trop long (limite description Discord = 4096)
        if len(error_trace) > 4000:
            error_trace = error_trace[-4000:]
            
        embed = {
            "title": "⚠️ Erreur Agend-INT",
            "description": f"Échec de la récupération des emplois du temps :\n```py\n{error_trace}\n```",
            "color": 16711680 # Rouge
        }
        
        response = requests.post(url, json={"embeds": [embed]})
        if response.status_code not in (200, 204):
            logging.error(f"Échec envoi erreur Discord: {response.status_code}")
    except Exception as e:
        logging.error(f"Impossible d'envoyer l'erreur via Discord: {e}")

def send_daily_schedule(schedules_dict, image_path=None):
    webhook_url = get_webhook_url()

    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(paris_tz)
    date_str = now.strftime("%d/%m/%Y")

    embed = {
        "title": f"📅 Emploi du temps du {date_str}",
        "color": 3447003, # Bleu
        "fields": [],
        "footer": {
            "text": "Agend-INT Bot • Planifié pour ~07h00 (Paris)"
        }
    }

    # Fusion des événements pour l'affichage Discord
    all_events = []
    for user_name, events in schedules_dict.items():
        all_events.extend(events)
        
    unique_events = {}
    for e in all_events:
        key = (e.start_time, e.end_time, e.name)
        if key not in unique_events:
            unique_events[key] = e
            
    merged_events = list(unique_events.values())
    merged_events.sort(key=lambda x: (x.start_time, x.name))

    if not merged_events:
        embed["description"] = "🎉 Aucun cours prévu aujourd'hui !"
        embed["color"] = 5763719 # Vert
    else:
        for event in merged_events:
            room = event.room if event.room else "Non spécifiée"
            if event.trainers:
                trainers = ", ".join(event.trainers)
            else:
                trainers = "Non spécifié"
                
            field_name = f"🕒 {event.start_time} - {event.end_time} | {event.type}"
            field_value = f"**Matière**: {event.name}\n**Salle**: {room}\n**Intervenant(s)**: {trainers}"
            
            embed["fields"].append({
                "name": field_name,
                "value": field_value,
                "inline": False
            })

    payload = {
        "embeds": [embed]
    }
    
    # Check if we have an image to upload
    if image_path and os.path.exists(image_path) and merged_events:
        filename = os.path.basename(image_path)
        embed["image"] = {"url": f"attachment://{filename}"}
        
        with open(image_path, "rb") as f:
            files = {
                "file": (filename, f, "image/png")
            }
            # When sending files, payload must be sent as multipart/form-data 'payload_json'
            response = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
    else:
        response = requests.post(webhook_url, json=payload)
        
    if response.status_code not in (200, 204):
        logging.error(f"Échec de l'envoi au webhook Discord (Code {response.status_code}):\n{response.text}")
    else:
        logging.info("Webhook envoyé avec succès.")
