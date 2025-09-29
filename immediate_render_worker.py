#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script immediato per processare le email inviate negli ultimi 10 giorni
Esegue l'intero flusso di automazione su un periodo esteso
"""

import os
import requests
import json
from datetime import datetime, timedelta
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
import sys
from config import MICROSOFT_GRAPH, GOOGLE_SHEETS, SYSTEM

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurazione da config.py
TENANT_ID = MICROSOFT_GRAPH['TENANT_ID']
CLIENT_ID = MICROSOFT_GRAPH['CLIENT_ID']
CLIENT_SECRET = MICROSOFT_GRAPH['CLIENT_SECRET']
SENDER_EMAIL = MICROSOFT_GRAPH['SENDER_EMAIL']

GOOGLE_SHEET_ID = GOOGLE_SHEETS['SHEET_ID']
SERVICE_ACCOUNT_FILE = GOOGLE_SHEETS['SERVICE_ACCOUNT_FILE']
MAIN_SHEET_NAME = GOOGLE_SHEETS['MAIN_SHEET_NAME']
BLACKLIST_SHEET_NAME = GOOGLE_SHEETS['BLACKLIST_SHEET_NAME']

# Configurazione sistema
TIMEZONE = SYSTEM['TIMEZONE']
SEARCH_KEYWORD = SYSTEM['SEARCH_KEYWORD']
WEEKS_BEFORE_FIRST_EMAIL = SYSTEM['WEEKS_BEFORE_FIRST_EMAIL']
WEEKS_BEFORE_SECOND_EMAIL = SYSTEM['WEEKS_BEFORE_SECOND_EMAIL']
FIRST_EMAIL_SUBJECT = SYSTEM['FIRST_EMAIL_SUBJECT']
FIRST_EMAIL_BODY = SYSTEM['FIRST_EMAIL_BODY']
SECOND_EMAIL_SUBJECT = SYSTEM['SECOND_EMAIL_SUBJECT']
SECOND_EMAIL_BODY = SYSTEM['SECOND_EMAIL_BODY']

# Timezone
ITALY_TZ = pytz.timezone(TIMEZONE)

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

def get_sent_emails_last_10_days(access_token):
    """Recupera le email inviate negli ultimi 10 giorni"""
    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/mailFolders/SentItems/messages"
    
    # Calcola la data di 10 giorni fa
    ten_days_ago = datetime.now(ITALY_TZ) - timedelta(days=10)
    filter_date = ten_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        '$filter': f"sentDateTime ge {filter_date}",
        '$orderby': 'sentDateTime desc',
        '$top': 100  # Limite ragionevole per 10 giorni
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
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione di Google Sheets: {e}")
        return None

def get_sheet_data(service):
    """Recupera i dati dal foglio principale"""
    try:
        range_name = f"{MAIN_SHEET_NAME}!A:D"
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=range_name
        ).execute()
        return result.get('values', [])
    except Exception as e:
        logger.error(f"Errore nel recupero dei dati del foglio: {e}")
        return []

def get_blacklist_emails(service):
    """Recupera la lista delle email in blacklist"""
    try:
        range_name = f"{BLACKLIST_SHEET_NAME}!A:A"
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=range_name
        ).execute()
        values = result.get('values', [])
        return [row[0].lower() for row in values if row and row[0]]
    except Exception as e:
        logger.error(f"Errore nel recupero della blacklist: {e}")
        return []

def add_email_to_sheet(service, email_address, blacklist):
    """Aggiunge un'email al foglio se non è in blacklist"""
    if email_address.lower() in blacklist:
        logger.info(f"Email {email_address} è in blacklist, saltata")
        return False
    
    # Controlla se l'email esiste già
    sheet_data = get_sheet_data(service)
    existing_emails = [row[0].lower() for row in sheet_data if row and row[0]]
    
    if email_address.lower() in existing_emails:
        logger.info(f"Email {email_address} già presente nel foglio")
        return False
    
    # Aggiunge la nuova email
    today = datetime.now(ITALY_TZ)
    today_str = today.strftime('%Y-%m-%d')
    
    new_row = [email_address, today_str, '', '']  # email, data aggiunta, prima email, seconda email
    
    try:
        range_name = f"{MAIN_SHEET_NAME}!A:D"
        body = {'values': [new_row]}
        service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        logger.info(f"Email {email_address} aggiunta al foglio")
        return True
    except Exception as e:
        logger.error(f"Errore nell'aggiunta dell'email {email_address}: {e}")
        return False

def update_sheet_cell(service, row, column, value):
    """Aggiorna una cella specifica nel foglio"""
    try:
        range_name = f"{MAIN_SHEET_NAME}!{column}{row}"
        body = {'values': [[value]]}
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=range_name,
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
    
    first_emails_sent = 0
    second_emails_sent = 0
    
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
                        first_emails_sent += 1
                
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
                            second_emails_sent += 1
                
                elif first_email_date and second_email_date:
                    logger.info(f"Entrambe le email già inviate a {email_address}")
                    
        except ValueError as e:
            logger.error(f"Errore nel parsing della data per {email_address}: {e}")
            continue
    
    return first_emails_sent, second_emails_sent

def main():
    """Funzione principale per processare le email degli ultimi 10 giorni"""
    logger.info("="*80)
    logger.info("IMMEDIATE RENDER WORKER - PROCESSAMENTO EMAIL ULTIMI 10 GIORNI")
    logger.info("="*80)
    logger.info(f"Account: {SENDER_EMAIL}")
    logger.info(f"Timestamp: {datetime.now(ITALY_TZ)}")
    logger.info(f"Periodo: ultimi 10 giorni")
    logger.info("")
    
    try:
        # Ottieni token di accesso
        logger.info("Connessione a Microsoft Graph...")
        access_token = get_access_token()
        if not access_token:
            logger.error("Impossibile ottenere token di accesso")
            return
        
        logger.info("✅ Token ottenuto con successo")
        
        # Inizializza Google Sheets
        logger.info("Connessione a Google Sheets...")
        sheets_service = get_google_sheets_service()
        if not sheets_service:
            logger.error("Impossibile inizializzare Google Sheets")
            return
        
        logger.info("✅ Google Sheets connesso con successo")
        
        # Fase 1: Controlla email inviate con keyword nel titolo negli ultimi 10 giorni
        logger.info(f"Fase 1: Controllo email inviate con '{SEARCH_KEYWORD}' nel titolo (ultimi 10 giorni)...")
        sent_emails = get_sent_emails_last_10_days(access_token)
        
        blacklist = get_blacklist_emails(sheets_service)
        logger.info(f"Blacklist caricata: {len(blacklist)} email")
        
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
        
        logger.info(f"✅ Trovate {facture_emails_found} nuove email con '{SEARCH_KEYWORD}' nel titolo")
        
        # Fase 2: Processa email di follow-up
        logger.info("Fase 2: Processamento email di follow-up...")
        first_emails_sent, second_emails_sent = process_follow_up_emails(access_token, sheets_service)
        
        logger.info(f"✅ Prima email inviate: {first_emails_sent}")
        logger.info(f"✅ Seconda email inviate: {second_emails_sent}")
        
        # Riepilogo finale
        logger.info("")
        logger.info("="*80)
        logger.info("RIEPILOGO PROCESSAMENTO")
        logger.info("="*80)
        logger.info(f"Email analizzate: {len(sent_emails)}")
        logger.info(f"Nuove email aggiunte: {facture_emails_found}")
        logger.info(f"Prime email inviate: {first_emails_sent}")
        logger.info(f"Seconde email inviate: {second_emails_sent}")
        logger.info(f"Account: {SENDER_EMAIL}")
        logger.info(f"Completato: {datetime.now(ITALY_TZ)}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    main()
