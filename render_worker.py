import os
import requests
import json
from datetime import datetime, timedelta
import time
import schedule
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
import sys

# Configurazione logging per Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurazione da variabili d'ambiente
TENANT_ID = os.getenv('TENANT_ID', 'ee6b29b7-6376-4655-9712-8096e78247f1')
CLIENT_ID = os.getenv('CLIENT_ID', '312ac792-f712-4e91-94ac-91f2d858b52b')
CLIENT_SECRET = os.getenv('CLIENT_SECRET', 'wCp8Q~GpDCnUDldqwe3P4oKV-I~0Bh5VnwmwLdkp')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'f.defin@defincouverture.fr')

GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1mSUd-XsPTABEbSZBc5whTdLUlid_Z0WbTIfsS4eXqUk')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

# Configurazione sistema
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Rome')
DAILY_TASK_TIME = os.getenv('DAILY_TASK_TIME', '06:00')
SEARCH_KEYWORD = os.getenv('SEARCH_KEYWORD', 'facture')
WEEKS_BEFORE_FIRST_EMAIL = int(os.getenv('WEEKS_BEFORE_FIRST_EMAIL', '2'))
WEEKS_BEFORE_SECOND_EMAIL = int(os.getenv('WEEKS_BEFORE_SECOND_EMAIL', '1'))

# Configurazione fogli
MAIN_SHEET_NAME = os.getenv('MAIN_SHEET_NAME', 'Foglio1')
BLACKLIST_SHEET_NAME = os.getenv('BLACKLIST_SHEET_NAME', 'Foglio2')

# Timezone
ITALY_TZ = pytz.timezone(TIMEZONE)

# Contenuti email
FIRST_EMAIL_SUBJECT = "Votre avis compte pour nous !"
FIRST_EMAIL_BODY = '''<html>
<body>
    <p>Bonjour,</p>
    
    <p>Vous avez récemment fait appel à nos services et nous espérons que tout s'est déroulé selon vos attentes et que vous êtes satisfait(e) du résultat.</p>
    
    <p>Pour continuer à offrir un service de qualité, nous serions ravis de connaître votre avis sur notre entreprise, nos équipes, et le travail réalisé. Cela nous permettrait d'améliorer encore notre savoir-faire et d'aider d'autres clients à faire leur choix.</p>
    
    <p>Vous pouvez laisser un avis en suivant ce lien : <a href="https://g.page/r/CVrzsUXQt-LIEBM/review">https://g.page/r/CVrzsUXQt-LIEBM/review</a></p>
    
    <p>Merci pour votre confiance et votre retour, qui nous est précieux !</p>
    
    <p>Bien cordialement,<br>
    L'équipe Defin Couverture</p>
</body>
</html>'''

SECOND_EMAIL_SUBJECT = "Un petit mot de votre part ? 😊"
SECOND_EMAIL_BODY = '''<html>
<body>
    <p>Bonjour,</p>
    
    <p>Il y a quelques semaines, nous vous avons envoyé un email pour recueillir votre avis sur notre intervention.</p>
    
    <p>Votre retour est important pour nous ! Il nous aide à continuer à améliorer nos services et à mieux répondre aux attentes de nos clients.</p>
    
    <p>Si vous n'avez pas encore eu l'occasion de partager votre expérience, vous pouvez le faire en quelques clics via ce lien : <a href="https://g.co/kgs/f4fM21Z">https://g.co/kgs/f4fM21Z</a><br>
    Cela ne prend qu'une minute, et votre témoignage sera d'une grande aide pour notre équipe.</p>
    
    <p>Merci d'avance pour votre temps et votre retour. N'hésitez pas à nous contacter si vous avez la moindre question ou besoin d'assistance supplémentaire.</p>
    
    <p>Bien cordialement,<br>
    L'équipe Defin Couverture</p>
</body>
</html>'''

def get_access_token():
    """Ottiene un token di accesso da Microsoft Graph"""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data['access_token']
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nell'ottenere il token di accesso: {e}")
        return None

def get_sent_emails_last_24h(access_token):
    """Recupera le email inviate nelle ultime 24 ore"""
    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/mailFolders/SentItems/messages"
    
    yesterday = datetime.now(ITALY_TZ) - timedelta(days=1)
    filter_date = yesterday.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        '$filter': f"sentDateTime ge {filter_date}",
        '$select': 'subject,toRecipients,sentDateTime'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('value', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nel recupero delle email inviate: {e}")
        return []

def get_google_sheets_service():
    """Inizializza il servizio Google Sheets"""
    try:
        if not GOOGLE_SERVICE_ACCOUNT_JSON:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON non configurato")
            
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione Google Sheets: {e}")
        return None

def get_blacklist_emails(service):
    """Recupera la lista delle email blacklisted"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{BLACKLIST_SHEET_NAME}!A:A'
        ).execute()
        
        blacklist = []
        if 'values' in result:
            blacklist = [row[0].lower().strip() for row in result['values'] if row and row[0].strip()]
        
        logger.info(f"Blacklist caricata: {len(blacklist)} email trovate")
        return blacklist
        
    except Exception as e:
        logger.error(f"Errore nel recupero blacklist: {e}")
        return []

def add_email_to_sheet(service, email_address, blacklist):
    """Aggiunge un indirizzo email al Google Sheet se non è blacklisted"""
    try:
        if email_address.lower().strip() in blacklist:
            logger.info(f"Email {email_address} non aggiunta perché blacklisted")
            return False
            
        today = datetime.now(ITALY_TZ).strftime('%Y-%m-%d')
        
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{MAIN_SHEET_NAME}!A:A'
        ).execute()
        
        existing_emails = []
        if 'values' in result:
            existing_emails = [row[0] for row in result['values'] if row]
        
        if email_address not in existing_emails:
            next_row = len(existing_emails) + 1
            
            body = {
                'values': [[email_address, today]]
            }
            
            service.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SHEET_ID,
                range=f'{MAIN_SHEET_NAME}!A{next_row}:B{next_row}',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Aggiunto {email_address} al Google Sheet")
            return True
        else:
            logger.info(f"Email {email_address} già presente nel sheet")
            return False
            
    except Exception as e:
        logger.error(f"Errore nell'aggiunta al Google Sheet: {e}")
        return False

def get_sheet_data(service):
    """Recupera tutti i dati dal Google Sheet"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{MAIN_SHEET_NAME}!A:D'
        ).execute()
        
        return result.get('values', [])
    except Exception as e:
        logger.error(f"Errore nel recupero dati dal Google Sheet: {e}")
        return []

def update_sheet_cell(service, row, column, value):
    """Aggiorna una cella specifica nel Google Sheet"""
    try:
        body = {
            'values': [[value]]
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{MAIN_SHEET_NAME}!{column}{row}',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return True
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento cella {column}{row}: {e}")
        return False

def send_email_with_graph(access_token, recipient, subject, body, is_html=False):
    """Invia un'email usando Microsoft Graph API"""
    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    content_type = "HTML" if is_html else "Text"
    
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": content_type,
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient
                    }
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=email_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nell'invio dell'email a {recipient}: {e}")
        return False

def process_follow_up_emails(access_token, service):
    """Processa le email di follow-up"""
    today = datetime.now(ITALY_TZ)
    today_str = today.strftime('%Y-%m-%d')
    
    sheet_data = get_sheet_data(service)
    
    for row_idx, row in enumerate(sheet_data, start=1):
        if len(row) == 0:
            continue
            
        email_address = row[0] if len(row) > 0 else ""
        date_added = row[1] if len(row) > 1 else ""
        first_email_date = row[2] if len(row) > 2 else ""
        second_email_date = row[3] if len(row) > 3 else ""
        
        if not email_address or not date_added:
            continue
            
        try:
            # Salta le righe con header
            if date_added.lower() in ['data', 'date', 'added on date']:
                continue
                
            added_date = datetime.strptime(date_added, '%Y-%m-%d')
            added_date = ITALY_TZ.localize(added_date)
            
            weeks_before_first = timedelta(weeks=WEEKS_BEFORE_FIRST_EMAIL)
            first_email_threshold = today - weeks_before_first
            
            if added_date <= first_email_threshold:
                # Prima email
                if not first_email_date:
                    if send_email_with_graph(
                        access_token, 
                        email_address, 
                        FIRST_EMAIL_SUBJECT, 
                        FIRST_EMAIL_BODY,
                        is_html=True
                    ):
                        update_sheet_cell(service, row_idx, 'C', today_str)
                        logger.info(f"Inviata prima email a {email_address}")
                
                # Seconda email
                elif first_email_date and not second_email_date:
                    first_date = datetime.strptime(first_email_date, '%Y-%m-%d')
                    first_date = ITALY_TZ.localize(first_date)
                    
                    weeks_before_second = timedelta(weeks=WEEKS_BEFORE_SECOND_EMAIL)
                    second_email_threshold = today - weeks_before_second
                    
                    if first_date <= second_email_threshold:
                        if send_email_with_graph(
                            access_token, 
                            email_address, 
                            SECOND_EMAIL_SUBJECT, 
                            SECOND_EMAIL_BODY,
                            is_html=True
                        ):
                            update_sheet_cell(service, row_idx, 'D', today_str)
                            logger.info(f"Inviata seconda email a {email_address}")
                
                elif first_email_date and second_email_date:
                    logger.info(f"Entrambe le email già inviate a {email_address}")
                    
        except ValueError as e:
            logger.error(f"Errore nel parsing della data per {email_address}: {e}")
            continue

def daily_task():
    """Task principale eseguito ogni giorno"""
    logger.info(f"=== INIZIO TASK GIORNALIERO - {datetime.now(ITALY_TZ)} ===")
    
    # Ottieni token di accesso
    access_token = get_access_token()
    if not access_token:
        logger.error("Impossibile ottenere il token di accesso. Uscita.")
        return
    
    # Inizializza Google Sheets
    sheets_service = get_google_sheets_service()
    if not sheets_service:
        logger.error("Impossibile inizializzare Google Sheets. Uscita.")
        return
    
    # Fase 1: Controlla email inviate con keyword nel titolo
    logger.info(f"Fase 1: Controllo email inviate con '{SEARCH_KEYWORD}' nel titolo...")
    sent_emails = get_sent_emails_last_24h(access_token)
    
    blacklist = get_blacklist_emails(sheets_service)
    
    facture_emails_found = 0
    for email in sent_emails:
        subject = email.get('subject', '').lower()
        if SEARCH_KEYWORD.lower() in subject:
            to_recipients = email.get('toRecipients', [])
            for recipient in to_recipients:
                email_address = recipient.get('emailAddress', {}).get('address', '')
                if email_address:
                    if add_email_to_sheet(sheets_service, email_address, blacklist):
                        facture_emails_found += 1
    
    logger.info(f"Trovate {facture_emails_found} nuove email con '{SEARCH_KEYWORD}' nel titolo")
    
    # Fase 2: Processa email di follow-up
    logger.info("Fase 2: Processamento email di follow-up...")
    process_follow_up_emails(access_token, sheets_service)
    
    logger.info(f"=== FINE TASK GIORNALIERO - {datetime.now(ITALY_TZ)} ===")

def health_check():
    """Health check per Render"""
    logger.info("Health check eseguito")
    return True

def main():
    """Funzione principale per Render worker"""
    logger.info("=== SISTEMA AUTOMATICO EMAIL H24 AVVIATO SU RENDER ===")
    logger.info(f"Ora corrente: {datetime.now(ITALY_TZ)}")
    logger.info(f"Task programmato per le {DAILY_TASK_TIME} ogni giorno (ora italiana)")
    
    # Programma il task
    schedule.every().day.at(DAILY_TASK_TIME).do(daily_task)
    
    # Health check ogni ora
    schedule.every().hour.do(health_check)
    
    # Esegui immediatamente per test (solo se specificato)
    if os.getenv('ENABLE_IMMEDIATE_TEST', 'false').lower() == 'true':
        logger.info("=== ESECUZIONE TEST IMMEDIATA ===")
        daily_task()
    
    # Loop principale ottimizzato per Render
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # Controlla ogni 30 secondi su Render
        except KeyboardInterrupt:
            logger.info("Sistema interrotto dall'utente")
            break
        except Exception as e:
            logger.error(f"Errore nel loop principale: {e}")
            time.sleep(300)  # Aspetta 5 minuti prima di riprovare

if __name__ == "__main__":
    main() 