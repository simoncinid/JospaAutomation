# Configurazione Microsoft Graph
MICROSOFT_GRAPH = {
    'TENANT_ID': "ee6b29b7-6376-4655-9712-8096e78247f1",
    'CLIENT_ID': "312ac792-f712-4e91-94ac-91f2d858b52b",
    'CLIENT_SECRET': "wCp8Q~GpDCnUDldqwe3P4oKV-I~0Bh5VnwmwLdkp",
    'SENDER_EMAIL': "contact@defincouverture.fr"
}

# Configurazione Google Sheets
GOOGLE_SHEETS = {
    'SHEET_ID': "1mSUd-XsPTABEbSZBc5whTdLUlid_Z0WbTIfsS4eXqUk",
    'SERVICE_ACCOUNT_FILE': "key-transformer-464915-j2-003c1648f096.json",
    'MAIN_SHEET_NAME': 'Foglio1',
    'BLACKLIST_SHEET_NAME': 'Foglio2'
}

# Configurazione sistema
SYSTEM = {
    'TIMEZONE': 'Europe/Rome',
    'DAILY_TASK_TIME': '06:00',
    'SEARCH_KEYWORD': 'facture',
    'WEEKS_BEFORE_FIRST_EMAIL': 2,
    'WEEKS_BEFORE_SECOND_EMAIL': 1,
    'FIRST_EMAIL_SUBJECT': 'Votre avis compte pour nous !',
    'FIRST_EMAIL_BODY': '''<html>
<body>
    <p>Bonjour,</p>
    
    <p>Vous avez récemment fait appel à nos services et nous espérons que tout s'est déroulé selon vos attentes et que vous êtes satisfait(e) du résultat.</p>
    
    <p>Pour continuer à offrir un service de qualité, nous serions ravis de connaître votre avis sur notre entreprise, nos équipes, et le travail réalisé. Cela nous permettrait d'améliorer encore notre savoir-faire et d'aider d'autres clients à faire leur choix.</p>
    
    <p>Vous pouvez laisser un avis en suivant ce lien : <a href="https://g.page/r/CVrzsUXQt-LIEBM/review">https://g.page/r/CVrzsUXQt-LIEBM/review</a></p>
    
    <p>Merci pour votre confiance et votre retour, qui nous est précieux !</p>
    
    <p>Bien cordialement,<br>
    L'équipe Defin Couverture</p>
</body>
</html>''',
    'SECOND_EMAIL_SUBJECT': 'Un petit mot de votre part ? 😊',
    'SECOND_EMAIL_BODY': '''<html>
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
</html>''',
    'ENABLE_IMMEDIATE_TEST': True  # Impostare False in produzione
}

# Configurazione logging
LOGGING = {
    'ENABLE_DETAILED_LOGS': True,
    'LOG_FILE': 'jospa_system.log'
} 