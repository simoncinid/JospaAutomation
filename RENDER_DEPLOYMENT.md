# Deployment su Render - Guida Completa

## Panoramica

Questa guida ti aiuterà a deployare il sistema automatico di email su Render come background worker.

## Prerequisiti

1. Account Render (gratuito): https://render.com
2. Repository GitHub con il codice
3. Credenziali Microsoft Graph
4. Credenziali Google Service Account

## File per Render

### File principali:
- `render_worker.py` - Worker principale ottimizzato per Render
- `requirements_render.txt` - Dipendenze con versioni fisse
- `render.yaml` - Configurazione Render (opzionale)

## Passaggi per il Deployment

### 1. Preparazione Repository

Assicurati che il repository GitHub contenga:
```
/
├── render_worker.py
├── requirements_render.txt
├── render.yaml (opzionale)
└── RENDER_DEPLOYMENT.md
```

### 2. Configurazione Render

1. **Accedi a Render**: https://dashboard.render.com
2. **Crea nuovo servizio**: Click "New" → "Background Worker"
3. **Connetti repository**: Seleziona il repository GitHub
4. **Configurazione base**:
   - **Name**: `jospa-email-worker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements_render.txt`
   - **Start Command**: `python render_worker.py`
   - **Plan**: `Starter` (gratuito)

### 3. Configurazione Variabili d'Ambiente

Nella sezione "Environment Variables", aggiungi:

#### Variabili Pubbliche:
```
TENANT_ID=ee6b29b7-6376-4655-9712-8096e78247f1
CLIENT_ID=312ac792-f712-4e91-94ac-91f2d858b52b
SENDER_EMAIL=f.defin@defincouverture.fr
GOOGLE_SHEET_ID=1mSUd-XsPTABEbSZBc5whTdLUlid_Z0WbTIfsS4eXqUk
TIMEZONE=Europe/Rome
DAILY_TASK_TIME=06:00
SEARCH_KEYWORD=facture
WEEKS_BEFORE_FIRST_EMAIL=2
WEEKS_BEFORE_SECOND_EMAIL=1
MAIN_SHEET_NAME=Foglio1
BLACKLIST_SHEET_NAME=Foglio2
ENABLE_IMMEDIATE_TEST=false
```

#### Variabili Segrete:
```
CLIENT_SECRET=wCp8Q~GpDCnUDldqwe3P4oKV-I~0Bh5VnwmwLdkp
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"key-transformer-464915-j2",...}
```

**IMPORTANTE**: Per `GOOGLE_SERVICE_ACCOUNT_JSON`, copia tutto il contenuto del file JSON in una singola riga.

### 4. Deploy

1. Click "Create Background Worker"
2. Render inizierà automaticamente il build e deploy
3. Monitora i log per verificare il corretto avvio

## Monitoraggio

### Log System
- Accedi ai log da Render Dashboard
- I log mostrano:
  - Avvio sistema
  - Esecuzione task giornalieri
  - Errori e successi
  - Health checks

### Esempio log di successo:
```
2024-01-15 06:00:00 - INFO - === INIZIO TASK GIORNALIERO ===
2024-01-15 06:00:01 - INFO - Blacklist caricata: 21 email trovate
2024-01-15 06:00:02 - INFO - Trovate 3 nuove email con 'facture' nel titolo
2024-01-15 06:00:03 - INFO - Inviata prima email a cliente@example.com
2024-01-15 06:00:04 - INFO - === FINE TASK GIORNALIERO ===
```

## Configurazione Avanzata

### Timezone
Il sistema usa `Europe/Rome` di default. Per cambiare:
```
TIMEZONE=Europe/Paris
```

### Orario Esecuzione
Per cambiare l'orario del task giornaliero:
```
DAILY_TASK_TIME=07:30
```

### Test Immediato
Per abilitare test immediato all'avvio (solo per debug):
```
ENABLE_IMMEDIATE_TEST=true
```

## Troubleshooting

### Errori Comuni

#### 1. Build Failed
```
Errore: pip install failed
Soluzione: Verifica requirements_render.txt
```

#### 2. Worker Crashed
```
Errore: Worker keeps restarting
Soluzione: Controlla variabili d'ambiente e log
```

#### 3. Google Sheets Permission Denied
```
Errore: 403 Forbidden
Soluzione: Condividi Google Sheet con service account email
```

#### 4. Microsoft Graph Unauthorized
```
Errore: 401 Unauthorized
Soluzione: Verifica CLIENT_SECRET non scaduto
```

### Debug Steps

1. **Controlla log Render**:
   - Dashboard → Service → Logs
   
2. **Verifica variabili d'ambiente**:
   - Dashboard → Service → Environment

3. **Test locale**:
   ```bash
   export TENANT_ID=...
   export CLIENT_ID=...
   # ... altre variabili
   python render_worker.py
   ```

## Costi

### Piano Starter (Gratuito):
- 750 ore/mese di runtime
- Perfetto per background worker
- Sufficiente per uso H24

### Limitazioni Piano Gratuito:
- Worker si spegne dopo 15 minuti di inattività
- Riavvio automatico quando necessario
- Nessun impatto sul funzionamento

## Backup e Sicurezza

### Backup Configurazione:
- Salva variabili d'ambiente
- Backup repository GitHub
- Documenta configurazioni personalizzate

### Sicurezza:
- Non committare mai secrets nel repository
- Usa variabili d'ambiente per dati sensibili
- Limita accesso al repository

## Aggiornamenti

### Per aggiornare il codice:
1. Push modifiche su GitHub
2. Render rileva automaticamente i cambiamenti
3. Redeploy automatico

### Per aggiornare configurazione:
1. Modifica variabili d'ambiente in Render
2. Riavvia il worker se necessario

## Supporto

### Risorse Utili:
- [Render Documentation](https://render.com/docs)
- [Python Workers Guide](https://render.com/docs/python-workers)
- [Environment Variables](https://render.com/docs/environment-variables)

### Contatto:
Per problemi specifici del codice, controlla i log e verifica la configurazione seguendo questa guida. 