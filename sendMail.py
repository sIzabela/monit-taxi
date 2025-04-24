import os
import json
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from dotenv import load_dotenv
from logFunctions import *

load_dotenv()
with open('config.json') as f:
    config = json.load(f)

def prepare_regionalny_mail(address):
    address = str(address)
    address = address.lower()
    address = address.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z').replace('_', '.')
    return address + '@unext.pl'

def send_email(i, sygnatura, data_zawarcia, nr_rej, poczatek_ochrony, mail_agenta):
    SENDER = os.getenv('SENDER_MONIT')
    SENDER_PASSWD = os.getenv('SENDER_MONIT_PASSWD')
    SUBJECT = config['mail_monitoring']['subject']

    with open('message.html', 'r') as f:
        mailContent = f.read()
    mailContent = mailContent.format(sygnatura=sygnatura, data_zawarcia=data_zawarcia, nr_rej=nr_rej, poczatek_ochrony=poczatek_ochrony)  # WERYFIKACJA WARTOŚCI WIADOMOŚCI

    email = EmailMessage()
    email["From"] = SENDER
    email["To"] = mail_agenta
    email["Subject"] = SUBJECT

    # Zaktualizuj treść HTML, aby odwoływała się do grafiki za pomocą CID
    image_cid = make_msgid(domain='example.com')
    mailContent = mailContent.replace('src="unext.png"', f'src="cid:{image_cid[1:-1]}"')

    # Dodaj alternatywną zawartość (HTML) do wiadomości e-mail
    email.add_alternative(mailContent, subtype='html')

    # Dodaj grafikę jako załącznik
    with open('unext.png', 'rb') as img:
        email.get_payload()[0].add_related(
            img.read(),
            maintype='image',
            subtype='png',
            cid=image_cid
        )

    try:
        smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
        smtp.starttls()
        smtp.login(SENDER, SENDER_PASSWD)
        log_message(f'{i}: > Wysyłanie maila do {mail_agenta}')
        smtp.sendmail(SENDER, mail_agenta, email.as_string())
        smtp.quit()
        return 0
    except Exception as e:
        log_message(f"Bład podczas wysyłania maila do {mail_agenta}: {e}")
        return 1