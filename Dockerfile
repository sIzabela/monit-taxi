# Dockerfile, Image, Container
FROM python:3.12-alpine

# Ustawienia katalogu roboczego
WORKDIR /app

# Instalacja niezbędnych narzędzi i bibliotek
RUN apk add --no-cache \
    rclone \
    curl \
    curl-dev \
    gcc \
    g++ \
    libc-dev \
    unixodbc-dev \
    gnupg \
    && \
    # Sprawdzenie architektury
    case $(uname -m) in \
        x86_64) architecture="amd64" ;; \
        arm64) architecture="arm64" ;; \
        *) architecture="unsupported" ;; \
    esac && \
    if [[ "unsupported" == "$architecture" ]]; then \
        echo "Alpine architecture $(uname -m) is not currently supported." && exit 1; \
    fi && \
    # Pobranie pakietów
    curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/msodbcsql18_18.4.1.1-1_$architecture.apk && \
    curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/mssql-tools18_18.4.1.1-1_$architecture.apk && \
    # (Opcjonalne) Weryfikacja podpisu
    curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/msodbcsql18_18.4.1.1-1_$architecture.sig && \
    curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/mssql-tools18_18.4.1.1-1_$architecture.sig && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --import - && \
    gpg --verify msodbcsql18_18.4.1.1-1_$architecture.sig msodbcsql18_18.4.1.1-1_$architecture.apk && \
    gpg --verify mssql-tools18_18.4.1.1-1_$architecture.sig mssql-tools18_18.4.1.1-1_$architecture.apk && \
    # Instalacja pakietów
    apk add --allow-untrusted msodbcsql18_18.4.1.1-1_$architecture.apk && \
    apk add --allow-untrusted mssql-tools18_18.4.1.1-1_$architecture.apk && \
    # Czyszczenie
    rm -f msodbcsql18_18.4.1.1-1_$architecture.apk mssql-tools18_18.4.1.1-1_$architecture.apk msodbcsql18_18.4.1.1-1_$architecture.sig mssql-tools18_18.4.1.1-1_$architecture.sig


# Kopiowanie plików aplikacji
COPY . .
# Skopiuj plik rclone.conf do kontenera
COPY rclone.conf /root/.config/rclone/rclone.conf

# Zaktualizuj pip
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Ustawienie PATH dla narzędzi MSSQL
ENV PATH="/opt/mssql-tools/bin:${PATH}"

# Komenda uruchamiająca aplikację
CMD ["python", "-u", "main.py"]