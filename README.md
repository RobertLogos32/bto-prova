# OTP Bot System

Un sistema di bot Telegram per la gestione di numeri telefonici e messaggi OTP per vari servizi di scommesse.

## Caratteristiche

- Flusso di autorizzazione utente tramite amministratori
- Richiesta e approvazione di numeri telefonici italiani
- Gestione di diversi servizi (bet365, Sisal, SNAI, Betflag)
- Ricezione automatica dei messaggi OTP
- Pannello amministrativo per la gestione di utenti e richieste

## Installazione e configurazione

### Prerequisiti

- Python 3.8 o superiore
- PostgreSQL Database (configurato su Render)
- Telegram Bot Token (ottenibile tramite BotFather)

### Istruzioni di configurazione

1. **Database PostgreSQL:**

   - Il database è già configurato su Render con il seguente URL:
   - `postgresql://otpbot:9LnkweXrxhITgJDeyZfTSIE58XAT4kBK@dpg-d0q357je5dus73ebqe20-a.oregon-postgres.render.com/otp_bot_db`
   - Il database verrà inizializzato automaticamente all'avvio dell'applicazione

2. **Configurazione del bot:**

   - Creare un nuovo bot su Telegram utilizzando [BotFather](https://t.me/botfather)
   - Copiare il token del bot
   - Modificare il file `config.py` inserendo il token del bot e gli ID degli amministratori

3. **Installare le dipendenze:**

   ```bash
   pip install -r requirements.txt
