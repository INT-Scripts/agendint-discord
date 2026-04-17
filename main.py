import sys
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
import datetime
from scraper import get_todays_schedules
from discord_bot import send_daily_schedule, send_error_to_discord
from image_generator import generate_multiple_schedules_image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("agendint.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

LAST_SUCCESS_DATE = None

def job(is_last_attempt=False):
    global LAST_SUCCESS_DATE
    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(paris_tz)
    
    if LAST_SUCCESS_DATE == now.date():
        logging.info("Exécution ignorée: déjà réussie aujourd'hui.")
        return

    logging.info("Exécution de la tâche planifiée...")
    try:
        # gets dict: { "User Name": [events...], ... }
        schedules_dict = get_todays_schedules()
        image_path = "schedule.png"
        generate_multiple_schedules_image(schedules_dict, image_path)
        send_daily_schedule(schedules_dict, image_path)
        LAST_SUCCESS_DATE = now.date()
        logging.info("Tâche exécutée avec succès !")
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de l'exécution : {e}", exc_info=True)
        if is_last_attempt:
            send_error_to_discord(e)

def main():
    load_dotenv()
    logging.info("Démarrage du bot Agendint-Discord...")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        logging.info("Paramètre --now détecté, exécution immédiate.")
        job(is_last_attempt=True)
        return

    paris_tz = pytz.timezone('Europe/Paris')
    scheduler = BlockingScheduler(timezone=paris_tz)
    
    # Planification à 6h50, 7h00 et 7h10
    scheduler.add_job(lambda: job(is_last_attempt=False), 'cron', hour=6, minute=50)
    scheduler.add_job(lambda: job(is_last_attempt=False), 'cron', hour=7, minute=0)
    scheduler.add_job(lambda: job(is_last_attempt=True), 'cron', hour=7, minute=10)
    
    logging.info("Planificateur démarré. Exécutions prévues à 06:50, 07:00, et 07:10 (Paris Time).")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Arrêt du bot.")

if __name__ == "__main__":
    main()
