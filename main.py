#Biblioteki do obsługi czasu
from datetime import datetime, timedelta
import time

#Biblioteki do obsługi plików i mail
from logFunctions import *
from getRaport import *
from sendMail import *
from ITmails import *
from rclone import *
import pandas as pd
import json
import os

with open('config.json') as f:
    config = json.load(f)

paths_date = datetime.datetime.now().strftime("%Y%m%d")

SP_PATH = config['paths']['sp_path']
SP_PATH_TEST = config['tests']['sp_path_test']
BASE_PATH = config['paths']['base_path'].format(paths_date=paths_date)
PLIK = config['paths']['baza_file'].format(base_path=BASE_PATH, paths_date=paths_date)
KONCOWY_FILE = config['paths']['koncowy_file'].format(paths_date=paths_date)

files_path = f"/app/files"
koncowy_path = f"{BASE_PATH}/{KONCOWY_FILE}"

# Sprawdzenie i tworzenie folderu z datą
os.makedirs(BASE_PATH, exist_ok=True)

# maile trybu DEBUG
TEST_MAIL_JEDEN = config['tests']['test_mail_jeden']
TEST_MAIL_KILKA = config['tests']['test_mail_kilka']

# ================================================== DEBUG ==================================================
DEBUG = config['debug'].lower() == 'true'  # tryb DEBUG
DEBUG_mails = config['debug_mails'].lower() == 'true'  # wysyłanie maili w trybie DEBUG
SP_UPLOAD = config['sp_upload'].lower() == 'true'  # czy wrzucać na SP

setup_logging()
log_message("Rozpoczynam prace tryb DEBUG: " + str(DEBUG))

if not DEBUG:
    if check_if_folder_exists(SP_PATH):
        log_message('Kończę działanie')
        exit(0)

start_time = time.time()

# Sprawdzenie, czy istnieje już plik końcowy i dopiero wtedy zaczynać pracę
if not os.path.isfile(koncowy_path):
    get_today_raport(PLIK)

    try:
        df = pd.read_excel(PLIK, sheet_name='Sheet1', dtype=str)
    except Exception as e:
        log_message('Błąd odczytu pliku wejściowego: ' + PLIK + ' - ' + str(e))
        exit(1)

    if DEBUG:  # DEBUG
        print(df.describe())
        print("\n========================================\n")
        print(df.head(5))
        print("========================================")

    ilosc_rekordow = str(len(df))
    log_message('Ilość rekordow do przeprocesowania: ' + ilosc_rekordow)

    df_koncowy = pd.DataFrame(columns=['SYGNATURA', 'DATA_ZAWARCIA', 'POCZATEK_OCHRONY', 'NR_REJESTRACYJNY', 'TAXI_INFO', 'MAIL_AGENTA', 'INFO'])
    # Obliczenie daty sprzed 365 dni
    one_year_ago = datetime.datetime.now() - timedelta(days=365)

    # Tworzenie pliku końcowego
    for i in range(len(df)):
        try:
            row = df.iloc[i]

            sygnatura = str(row['SYGNATURA'])
            data_zawarcia = pd.to_datetime(row['DATA_ZAWARCIA']).strftime('%Y-%m-%d')
            poczatek_ochrony = pd.to_datetime(row['POCZATEK_OCHRONY']).strftime('%Y-%m-%d')
            nr_rej = row['NR_REJESTRACYJNY']
            taxi_info = row['TAXI_INFO']
            mail_agenta = row['MAIL_AGENTA']


            taxi_date_str = taxi_info.split(" ")[1].strip("()")
            taxi_date = datetime.datetime.strptime(taxi_date_str, "%d.%m.%Y")

            # Sprawdzenie, czy data mieści się w zakresie
            taxi_check = taxi_date >= one_year_ago

            if taxi_check:
                df_koncowy.loc[len(df_koncowy)] = [sygnatura, data_zawarcia, poczatek_ochrony, nr_rej, taxi_info, mail_agenta, ""]
                df_koncowy.to_excel(koncowy_path, index=False)

        except Exception as e:
            error_log = f'Bład podczas przetwarzania rekordu {sygnatura} - INDEX {i}: {e}'
            log_message(error_log)
            if not DEBUG:
                send_error_email(error_log)
            exit(1)

    # Obsługa wysyłki maili
    log_message('Rozpoczynam wysyłkę maili')
    for i, row in df_koncowy.iterrows():
        if DEBUG:
            if DEBUG_mails:
                mail_agenta = TEST_MAIL_JEDEN
                result = send_email(i, sygnatura, data_zawarcia, nr_rej, poczatek_ochrony, mail_agenta)
            else:
                result = 2
        else:
            result = send_email(i, sygnatura, data_zawarcia, nr_rej, poczatek_ochrony, mail_agenta)
        
        
        if result == 0:
            row['INFO'] = 'OK: wysłano wiadomość MAIL'
        elif result == 2:
            log_message(f'{i}: DEBUG: obsługa bez mailingu')
            row['INFO'] = 'DEBUG: obsługa bez mailingu'
        else:
            row['INFO'] = 'PROBLEM: nie wysłano wiadomości MAIL'

        df_koncowy.to_excel(koncowy_path, index=False)
            
else:  # Wznawianie przerwanej pracy na wysyłce maili
    log_message(f'Plik końcowy {koncowy_path} już istnieje - kontynuuję wysyłkę maili.')
    df_koncowy = pd.read_excel(koncowy_path)

    for i, row in df_koncowy.iterrows():
        if pd.isna(row['INFO']) or row['INFO'].strip() == '':
            sygnatura = row['SYGNATURA']
            data_zawarcia = pd.to_datetime(row['DATA_ZAWARCIA']).strftime('%Y-%m-%d')
            poczatek_ochrony = pd.to_datetime(row['POCZATEK_OCHRONY']).strftime('%Y-%m-%d')
            nr_rej = row['NR_REJESTRACYJNY']
            mail_agenta = row['MAIL_AGENTA']

            if DEBUG:
                if DEBUG_mails:
                    mail_agenta = TEST_MAIL_JEDEN
                    log_message(f'{i}: DEBUG: Wysyłanie maila do {mail_agenta}')
                    result = send_email(i, sygnatura, data_zawarcia, nr_rej, poczatek_ochrony, mail_agenta)
                else:
                    result = 2
            else:
                log_message(f'{i}: Wysyłanie maila do {mail_agenta}')
                result = send_email(i, sygnatura, data_zawarcia, nr_rej, poczatek_ochrony, mail_agenta)
            
            
            if result == 0:
                log_message(f'{i}: Wysłano maila do {mail_agenta}')
                df_koncowy.loc[i, 'INFO'] = 'OK: wysłano wiadomość MAIL'
            elif result == 2:
                log_message(f'{i}: DEBUG: obsługa bez mailingu')
                df_koncowy.loc[i, 'INFO'] = 'DEBUG: obsługa bez mailingu'
            else:
                log_message(f'{i}: Błąd podczas wysyłania maila do {mail_agenta}')
                df_koncowy.loc[i, 'INFO'] = 'PROBLEM: nie wysłano wiadomości MAIL'

            df_koncowy.to_excel(koncowy_path, index=False)


if DEBUG:
    send_end_debug(koncowy_path, KONCOWY_FILE, DEBUG_mails, ilosc_rekordow)
    if SP_UPLOAD:
        log_message('Rozpoczynam kopiowanie plików do folderu na SP')
        upload_success = upload_to_SP(BASE_PATH, SP_PATH_TEST)
        if not upload_success:
            error_msg = "Rclone: Błąd przesyłania folderu na SP. Sprawdź logi."
            log_message(error_msg)
            send_error_email(error_msg)
else:
    if SP_UPLOAD:
        log_message('Rozpoczynam kopiowanie plików do folderu na SP')
        upload_success = upload_to_SP(BASE_PATH, SP_PATH)
        if not upload_success:
            error_msg = "Rclone: Błąd przesyłania folderu na SP. Sprawdź logi."
            log_message(error_msg)
            send_error_email(error_msg)

    log_message('Rozpoczynanie wysyłki maili')
    send_end_email(koncowy_path, KONCOWY_FILE, paths_date, ilosc_rekordow)

    remove_old_logs()

log_message('Czas wykonania: ' + str(round(time.time() - start_time, 2)))