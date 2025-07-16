# Guida al Deployment - Sistema H24

## Prerequisiti

### Software necessario:
- Python 3.8 o superiore
- Connessione internet stabile
- Accesso a Remote Desktop Windows

### Credenziali necessarie:
- Microsoft Graph Application configurata
- Google Service Account con accesso al Google Sheet
- Utente email valido nel tenant Microsoft 365

## Installazione

### 1. Preparazione ambiente
```bash
# Clona/copia i file del progetto
cd C:\jospa

# Installa le dipendenze
pip install -r requirements.txt
```

### 2. Verifica file di configurazione
Assicurati che siano presenti:
- `jospa.py` - Script principale
- `config.py` - Configurazione
- `key-transformer-464915-j2-003c1648f096.json` - Credenziali Google
- `requirements.txt` - Dipendenze

### 3. Test iniziale
```bash
# Test rapido (esegue il task immediatamente)
python jospa.py
```

## Configurazione per Produzione

### 1. Modifica config.py
```python
SYSTEM = {
    # ... altre configurazioni ...
    'ENABLE_IMMEDIATE_TEST': False  # Disabilita test immediato
}
```

### 2. Configurazione orario
Il sistema è configurato per l'orario italiano (Europe/Rome).
Task programmato per le 6:00 ogni mattina.

### 3. Avvio automatico Windows

#### Opzione A: Task Scheduler
1. Apri Task Scheduler
2. Crea Task Base
3. Trigger: Daily alle 5:55 AM
4. Action: Start Program
   - Program: `python.exe`
   - Arguments: `C:\jospa\jospa.py`
   - Start in: `C:\jospa`

#### Opzione B: Servizio Windows
Usa `start_system.bat` per avvio manuale.

## Monitoraggio

### Log System
Il sistema genera log dettagliati in `jospa_system.log`.

### Controlli da fare:
1. **Connessione Microsoft Graph**: Verifica token di accesso
2. **Connessione Google Sheets**: Verifica service account
3. **Invio email**: Controlla log per errori
4. **Google Sheet**: Verifica aggiornamenti dati

## Struttura Google Sheet

| Colonna | Descrizione | Formato |
|---------|-------------|---------|
| A | Indirizzo email destinatario | email@domain.com |
| B | Data aggiunta al sheet | YYYY-MM-DD |
| C | Data invio prima email | YYYY-MM-DD |
| D | Data invio seconda email | YYYY-MM-DD |

## Troubleshooting

### Errori comuni:

#### 1. Token Microsoft Graph scaduto
```
Errore: 401 Unauthorized
Soluzione: Verificare CLIENT_SECRET non scaduto
```

#### 2. Google Service Account non autorizzato
```
Errore: 403 Forbidden
Soluzione: Condividere Google Sheet con service account email
```

#### 3. Utente email non trovato
```
Errore: 404 Not Found
Soluzione: Verificare che sender_email esista nel tenant
```

#### 4. Timezone non corretto
```
Problema: Task eseguito all'ora sbagliata
Soluzione: Verificare timezone del server
```

## Manutenzione

### Controlli settimanali:
- [ ] Verifica log errori
- [ ] Controllo Google Sheet aggiornamenti
- [ ] Test invio email manuale

### Controlli mensili:
- [ ] Verifica scadenza CLIENT_SECRET
- [ ] Backup configurazione
- [ ] Pulizia log vecchi

## Backup e Ripristino

### File da backuppare:
- `jospa.py`
- `config.py`
- `key-transformer-464915-j2-003c1648f096.json`
- `requirements.txt`

### Ripristino:
1. Copia file di backup
2. Installa dipendenze: `pip install -r requirements.txt`
3. Avvia sistema: `python jospa.py`

## Sicurezza

### Protezione credenziali:
- Non condividere file JSON service account
- Proteggere CLIENT_SECRET
- Limitare accesso alla cartella del progetto

### Permessi minimi:
- Microsoft Graph: Mail.Send, Mail.Read, User.Read.All
- Google Sheets: spreadsheets scope

## Supporto

Per problemi tecnici:
1. Controlla log sistema
2. Verifica connessioni API
3. Testa componenti singolarmente 