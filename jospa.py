import requests
import json
from datetime import datetime, timedelta
import time
import schedule
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import MICROSOFT_GRAPH, GOOGLE_SHEETS, SYSTEM, LOGGING

# Configurazione da config.py
TENANT_ID = MICROSOFT_GRAPH['TENANT_ID']
CLIENT_ID = MICROSOFT_GRAPH['CLIENT_ID']
CLIENT_SECRET = MICROSOFT_GRAPH['CLIENT_SECRET']
sender_email = MICROSOFT_GRAPH['SENDER_EMAIL']

GOOGLE_SHEET_ID = GOOGLE_SHEETS['SHEET_ID']
SERVICE_ACCOUNT_FILE = GOOGLE_SHEETS['SERVICE_ACCOUNT_FILE']
MAIN_SHEET_NAME = GOOGLE_SHEETS['MAIN_SHEET_NAME']
BLACKLIST_SHEET_NAME = GOOGLE_SHEETS['BLACKLIST_SHEET_NAME']

# Timezone italiana
ITALY_TZ = pytz.timezone(SYSTEM['TIMEZONE'])

def get_access_token():
    """Ottiene un token di accesso da Microsoft Graph usando Client Credentials Flow"""
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
        print(f"Errore nell'ottenere il token di accesso: {e}")
        return None

def get_sent_emails_last_24h(access_token):
    """Recupera le email inviate nelle ultime 24 ore"""
    url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/mailFolders/SentItems/messages"
    
    # Calcola la data di 24 ore fa
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
        print(f"Errore nel recupero delle email inviate: {e}")
        return []

def get_google_sheets_service():
    """Inizializza il servizio Google Sheets"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"Errore nell'inizializzazione Google Sheets: {e}")
        return None

def get_blacklist_emails(service):
    """Recupera la lista delle email blacklisted dal Foglio2"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{BLACKLIST_SHEET_NAME}!A:A'
        ).execute()
        
        blacklist = []
        if 'values' in result:
            blacklist = [row[0].lower().strip() for row in result['values'] if row and row[0].strip()]
        
        print(f"Blacklist caricata: {len(blacklist)} email trovate")
        return blacklist
        
    except Exception as e:
        print(f"Errore nel recupero blacklist: {e}")
        return []

def add_email_to_sheet(service, email_address, blacklist):
    """Aggiunge un indirizzo email al Google Sheet se non è blacklisted"""
    try:
        # Controlla se l'email è nella blacklist
        if email_address.lower().strip() in blacklist:
            print(f"Email {email_address} non aggiunta perché blacklisted")
            return False
            
        today = datetime.now(ITALY_TZ).strftime('%Y-%m-%d')
        
        # Leggi i dati esistenti per evitare duplicati
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{MAIN_SHEET_NAME}!A:A'
        ).execute()
        
        existing_emails = []
        if 'values' in result:
            existing_emails = [row[0] for row in result['values'] if row]
        
        # Aggiungi solo se non esiste già
        if email_address not in existing_emails:
            # Trova la prima riga vuota
            next_row = len(existing_emails) + 1
            
            # Aggiungi email e data
            body = {
                'values': [[email_address, today]]
            }
            
            service.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SHEET_ID,
                range=f'{MAIN_SHEET_NAME}!A{next_row}:B{next_row}',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"Aggiunto {email_address} al Google Sheet")
            return True
        else:
            print(f"Email {email_address} già presente nel sheet")
            return False
            
    except Exception as e:
        print(f"Errore nell'aggiunta al Google Sheet: {e}")
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
        print(f"Errore nel recupero dati dal Google Sheet: {e}")
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
        print(f"Errore nell'aggiornamento cella {column}{row}: {e}")
        return False

def send_email_with_graph(access_token, recipient, subject, body, is_html=False):
    """Invia un'email usando Microsoft Graph API"""
    url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
    
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
        print(f"Errore nell'invio dell'email a {recipient}: {e}")
        return False

def process_follow_up_emails(access_token, service):
    """Processa le email di follow-up basate sui dati del Google Sheet"""
    today = datetime.now(ITALY_TZ)
    today_str = today.strftime('%Y-%m-%d')
    
    # Recupera i dati dal sheet
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
            # Converti la data di aggiunta
            added_date = datetime.strptime(date_added, '%Y-%m-%d')
            added_date = ITALY_TZ.localize(added_date)
            
            # Controlla se sono passate almeno 2 settimane
            weeks_before_first = timedelta(weeks=SYSTEM['WEEKS_BEFORE_FIRST_EMAIL'])
            first_email_threshold = today - weeks_before_first
            
            if added_date <= first_email_threshold:
                # Caso 1: Colonna C vuota - invia prima email
                if not first_email_date:
                    if send_email_with_graph(
                        access_token, 
                        email_address, 
                        SYSTEM['FIRST_EMAIL_SUBJECT'], 
                        SYSTEM['FIRST_EMAIL_BODY'],
                        is_html=True
                    ):
                        update_sheet_cell(service, row_idx, 'C', today_str)
                        print(f"Inviata prima email a {email_address}")
                
                # Caso 2: Colonna C piena, D vuota - controlla se è passata 1 settimana
                elif first_email_date and not second_email_date:
                    first_date = datetime.strptime(first_email_date, '%Y-%m-%d')
                    first_date = ITALY_TZ.localize(first_date)
                    
                    weeks_before_second = timedelta(weeks=SYSTEM['WEEKS_BEFORE_SECOND_EMAIL'])
                    second_email_threshold = today - weeks_before_second
                    
                    if first_date <= second_email_threshold:
                        if send_email_with_graph(
                            access_token, 
                            email_address, 
                            SYSTEM['SECOND_EMAIL_SUBJECT'], 
                            SYSTEM['SECOND_EMAIL_BODY'],
                            is_html=True
                        ):
                            update_sheet_cell(service, row_idx, 'D', today_str)
                            print(f"Inviata seconda email a {email_address}")
                
                # Caso 3: Entrambe le colonne C e D piene - non fare nulla
                elif first_email_date and second_email_date:
                    print(f"Entrambe le email già inviate a {email_address}")
                    
        except ValueError as e:
            print(f"Errore nel parsing della data per {email_address}: {e}")
            continue

def daily_task():
    """Task principale eseguito ogni giorno alle 6:00"""
    print(f"=== INIZIO TASK GIORNALIERO - {datetime.now(ITALY_TZ)} ===")
    
    # Ottieni token di accesso
    access_token = get_access_token()
    if not access_token:
        print("Impossibile ottenere il token di accesso. Uscita.")
        return
    
    # Inizializza Google Sheets
    sheets_service = get_google_sheets_service()
    if not sheets_service:
        print("Impossibile inizializzare Google Sheets. Uscita.")
        return
    
    # Fase 1: Controlla email inviate con "facture" nel titolo
    print("Fase 1: Controllo email inviate con 'facture' nel titolo...")
    sent_emails = get_sent_emails_last_24h(access_token)
    
    facture_emails_found = 0
    # Carica la blacklist
    blacklist = get_blacklist_emails(sheets_service)
    
    for email in sent_emails:
        subject = email.get('subject', '').lower()
        if SYSTEM['SEARCH_KEYWORD'].lower() in subject:
            # Estrai gli indirizzi email dei destinatari
            to_recipients = email.get('toRecipients', [])
            for recipient in to_recipients:
                email_address = recipient.get('emailAddress', {}).get('address', '')
                if email_address:
                    if add_email_to_sheet(sheets_service, email_address, blacklist):
                        facture_emails_found += 1
    
    print(f"Trovate {facture_emails_found} nuove email con '{SYSTEM['SEARCH_KEYWORD']}' nel titolo")
    
    # Fase 2: Processa email di follow-up
    print("Fase 2: Processamento email di follow-up...")
    process_follow_up_emails(access_token, sheets_service)
    
    print(f"=== FINE TASK GIORNALIERO - {datetime.now(ITALY_TZ)} ===\n")

def main():
    """Funzione principale che programma il task giornaliero"""
    print("=== SISTEMA AUTOMATICO EMAIL H24 AVVIATO ===")
    print(f"Ora corrente: {datetime.now(ITALY_TZ)}")
    print(f"Task programmato per le {SYSTEM['DAILY_TASK_TIME']} ogni giorno (ora italiana)")
    print("Premere Ctrl+C per interrompere\n")
    
    # Programma il task per l'orario configurato ogni giorno
    schedule.every().day.at(SYSTEM['DAILY_TASK_TIME']).do(daily_task)
    
    # Esegui immediatamente per test (se abilitato)
    if SYSTEM['ENABLE_IMMEDIATE_TEST']:
        print("=== ESECUZIONE TEST IMMEDIATA ===")
        daily_task()
    
    # Loop principale
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Controlla ogni minuto
        except KeyboardInterrupt:
            print("\nSistema interrotto dall'utente")
            break
        except Exception as e:
            print(f"Errore nel loop principale: {e}")
            time.sleep(300)  # Aspetta 5 minuti prima di riprovare

if __name__ == "__main__":
    main()
