# Sistema Automatico H24 - Email e Google Sheets

Questo progetto è un sistema automatico che gira H24 su remote desktop e gestisce:
1. Monitoraggio email inviate con "facture" nel titolo
2. Aggiornamento automatico Google Sheets
3. Invio email di follow-up automatiche

Utilizza Microsoft Graph API per le email e Google Sheets API per i dati.

## Configurazione

### Credenziali Microsoft Graph configurate:
- **Nome applicazione**: MICROSOFT_GRAPH
- **Application ID**: 312ac792-f712-4e91-94ac-91f2d858b52b
- **Tenant ID**: ee6b29b7-6376-4655-9712-8096e78247f1
- **Client Secret**: wCp8Q~GpDCnUDldqwe3P4oKV-I~0Bh5VnwmwLdkp
- **Scadenza secret**: 18/06/2027

### Google Sheets configurato:
- **Sheet ID**: 1mSUd-XsPTABEbSZBc5whTdLUlid_Z0WbTIfsS4eXqUk
- **Service Account**: diego-382@key-transformer-464915-j2.iam.gserviceaccount.com

### Utenti disponibili nel tenant:
- f.defin@defincouverture.fr (utilizzato come mittente)
- archive-contact@defincouverture.fr
- compta@defincouverture.fr
- contact@defincouverture.fr

## Installazione

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Utilizzo

### Avvio del sistema H24:
```bash
python jospa.py
```

Il sistema:
1. **Alle 6:00 ogni mattina (ora italiana)**:
   - Controlla email inviate nelle ultime 24h con "facture" nel titolo
   - Aggiunge i destinatari al Google Sheet (colonna A) con data (colonna B)
   
2. **Dopo il controllo email**:
   - Controlla righe con date ≥ 2 settimane fa
   - Se colonna C vuota → invia email "1" con testo "email 1"
   - Se colonna C piena e D vuota e ≥ 1 settimana → invia email "2" con testo "email 2"
   - Se entrambe le colonne piene → non fa nulla

### Struttura Google Sheet:
- **Colonna A**: Indirizzo email destinatario
- **Colonna B**: Data aggiunta al sheet
- **Colonna C**: Data invio prima email di follow-up
- **Colonna D**: Data invio seconda email di follow-up

## Funzionalità

- ✅ Sistema automatico H24 con scheduler
- ✅ Monitoraggio email inviate con "facture" nel titolo
- ✅ Integrazione Google Sheets per tracking
- ✅ Sistema di follow-up automatico a 2 livelli
- ✅ Gestione timezone italiana
- ✅ Autenticazione automatica Microsoft Graph e Google
- ✅ Prevenzione duplicati nel Google Sheet
- ✅ Gestione errori completa e logging
- ✅ Test immediato all'avvio (rimovibile in produzione)

## Permessi richiesti

### Microsoft Graph:
- `Mail.Send` - Per inviare email di follow-up
- `Mail.Read` - Per leggere email inviate
- `User.Read.All` - Per verificare l'esistenza degli utenti

### Google Sheets:
- `https://www.googleapis.com/auth/spreadsheets` - Per leggere/scrivere nel Google Sheet

## Struttura del progetto

```
jospa/
├── jospa.py                                    # Script principale H24
├── requirements.txt                            # Dipendenze Python
├── key-transformer-464915-j2-003c1648f096.json # Credenziali Google Service Account
├── README.md                                   # Documentazione
└── jospa.txt                                   # Dati delle tariffe (non utilizzato)
```

## Risoluzione problemi

### Errore 404 - Utente non trovato
Assicurati che l'indirizzo email del mittente sia presente nel tenant Microsoft 365.

### Errore di autenticazione
Verifica che:
- Le credenziali siano corrette
- Il secret non sia scaduto
- L'applicazione abbia i permessi necessari

### Errore di invio
Controlla che:
- Il mittente abbia i permessi per inviare email
- Il formato dell'email sia corretto
- La connessione internet sia attiva 