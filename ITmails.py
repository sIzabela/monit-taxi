from dotenv import load_dotenv
import os
import json
import smtplib
from email.message import EmailMessage
from logFunctions import *
from datetime import datetime, timedelta

def generate_dates():
    today = datetime.now()
    data_start = (today - timedelta(days=7)).strftime("%d.%m.%Y")
    data_koniec = (today - timedelta(days=1)).strftime("%d.%m.%Y")
    return data_start, data_koniec


def send_end_email(koncowy_path, koncowy_file, paths_date, ilosc_rekordow):
    load_dotenv()
    with open('config.json') as f:
        config = json.load(f)

    data_start, data_koniec = generate_dates()

    log_message('Przygotowanie maila końcowego')
    SENDER = os.getenv('SENDER_IT')
    SENDER_PASSWD = os.getenv('SENDER_IT_PASSWD')
    RECIPIENTS = config['mail_robot']['recipients']
    SUBJECT = config['mail_robot']['end_mail_subject']
    MESSAGE = config['mail_robot']['end_mail_body'].format(paths_date=paths_date, data_start=data_start, data_koniec=data_koniec, ilosc_rekordow=ilosc_rekordow)

    email = EmailMessage()
    email["From"] = SENDER
    email["To"] = ", ".join(RECIPIENTS)
    email["Subject"] = SUBJECT
    email.set_content(MESSAGE)
    if os.path.isfile(koncowy_path):
        with open(koncowy_path, "rb") as f:
            email.add_attachment(
                f.read(),
                filename = koncowy_file,
                maintype ="application",
                subtype ="xlsx"
            )

    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(SENDER, SENDER_PASSWD)
    for recipient in RECIPIENTS:
        log_message(f'Wysyłanie maila do {recipient}')
        smtp.sendmail(SENDER, recipient.strip(), email.as_string())
    smtp.quit()
    log_message('Zakończono wysyłkę maili')


def send_error_email(error):
    load_dotenv()
    with open('config.json') as f:
        config = json.load(f)

    log_message('Przygotowanie maila z opisem błędu')
    SENDER = os.getenv('SENDER_IT')
    SENDER_PASSWD = os.getenv('SENDER_IT_PASSWD')
    RECIPIENTS = config['mail_robot']['it_recipients']
    SUBJECT = config['mail_robot']['error_mail_subject']
    MESSAGE = config['mail_robot']['error_mail_body'].format(error=error)

    email = EmailMessage()
    email["From"] = SENDER
    email["To"] = ", ".join(RECIPIENTS)
    email["Subject"] = SUBJECT
    email.set_content(MESSAGE)

    # log_message('>> Łączenie do serwera smtp')
    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(SENDER, SENDER_PASSWD)
    for recipient in RECIPIENTS:
        log_message(f'Wysyłanie maila do {recipient}')
        smtp.sendmail(SENDER, recipient.strip(), email.as_string())
    smtp.quit()
    log_message('Zakończono wysyłkę maili z opisem błędu')

def send_end_debug(koncowy_path, koncowy_file, DEBUG_mails, ilosc_rekordow):
    load_dotenv()
    with open('config.json') as f:
        config = json.load(f)

    data_start, data_koniec = generate_dates()

    log_message('Przygotowanie maila końcowego')
    SENDER = os.getenv('SENDER_IT')
    SENDER_PASSWD = os.getenv('SENDER_IT_PASSWD')
    RECIPIENTS = config['mail_robot']['it_recipients']
    SUBJECT = config['mail_robot']['end_debug_subject']
    MESSAGE = config['mail_robot']['end_debug_body'].format(DEBUG_mails=DEBUG_mails, data_start=data_start, data_koniec=data_koniec, ilosc_rekordow=ilosc_rekordow)

    email = EmailMessage()
    email["From"] = SENDER
    email["To"] = ", ".join(RECIPIENTS)
    email["Subject"] = SUBJECT
    email.set_content(MESSAGE)
    if os.path.isfile(koncowy_path):
        with open(koncowy_path, "rb") as f:
            email.add_attachment(
                f.read(),
                filename = koncowy_file,
                maintype ="application",
                subtype ="xlsx"
            )

    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(SENDER, SENDER_PASSWD)
    for recipient in RECIPIENTS:
        log_message(f'Wysyłanie maila do {recipient}')
        smtp.sendmail(SENDER, recipient.strip(), email.as_string())
    smtp.quit()
    log_message('Zakończono wysyłkę maili')