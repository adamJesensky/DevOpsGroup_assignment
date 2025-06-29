# Section 1: Dockerizácia Python Web Aplikácie

## Prehľad Zadania

Cieľom tejto úlohy je zabaliť jednoduchú webovú aplikáciu napísanú v Pythone do Docker. Výsledkom je prenosné a izolovane spustiteľné prostredie pre aplikáciu.

### 1. Aplikácia (`app/app.py`)

- Základná webová aplikácia. Používa **Flask**.
- `@app.route('/')`: Tento riadok hovori, že keď niekto navštívi hlavnú stránku (napr. `http://localhost:5000/`), má sa spustiť funkcia `hello()`.
- `return "Hello World :D!"`: Funkcia vráti tento text, ktorý sa zobrazí v prehliadači.
- `app.run(host='0.0.0.0')`: Toto je kľúčové pre Docker. `0.0.0.0` znamená, že server počúva na všetkých sieťových rozhraniach v kontajneri. Keby sme použili predvolené `127.0.0.1` (localhost), aplikácia by bola dostupná len *vnútri* kontajnera a my by sme sa k nej z nášho počítača nedostali.

### 2. Závislosti (`app/requirements.txt`)

- spôsob ako definovať, ktoré knižnice aplikácia potrebuje.
- Zabezpečuje, že každý, kto spustí vašu aplikáciu (alebo Docker, ktorý ju buildí), nainštaluje presne tú istú verziu knižníc. Tým sa predchádza chybám typu "u mňa to funguje".

### 3. Dockerfile

- Recept alebo návod pre Docker, ako postaviť našu aplikáciu. Obraz je šablóna, z ktorej sa potom vytvárajú kontajnery.
- Multi-stage build:
    1.  **Prvá fáza (`builder`):**
        - `FROM python:3.9-slim as builder`: Začneme s oficiálnym Pythonom. Tento obraz obsahuje všetky nástroje potrebné na inštaláciu knižníc (ako `pip`).
        - `COPY app/requirements.txt .`: Skopírujeme len `requirements.txt`.
        - `RUN pip install ...`: Nainštalujeme závislosti. Tieto sa nainštalujú do dočasného prostredia fázy `builder`.
    2.  **Druhá fáza:**
        - `FROM python:3.9-slim`: Začneme znova s čistým, malým Python obrazom. Tento už neobsahuje zbytočné build nástroje.
        - `COPY --from=builder ...`: Skopírujeme **iba nainštalované knižnice** z predchádzajúcej fázy. Nezoberieme so sebou žiadny inštalačný BS.
        - `COPY app/app.py .`: Skopírujeme našu aplikáciu.

### 4. Docker Compose (`docker-compose.yml`)

- Nástroj na definovanie a spúšťanie viackontajnerových Docker aplikácií. Aj keď máme len jeden kontajner, `docker-compose` zjednodušuje jeho správu.
- `services`: Definuje jednotlivé služby (v našom prípade len jednu, `web`).
- `build: .`: Hovorí `docker-compose`, aby postavil obraz z `Dockerfile` v aktuálnom priečinku.
- `ports: - "5000:5000"`: Toto je presmerovanie portov. Mapuje port `5000` na našom počítači (prvé číslo) na port `5000` vnútri kontajnera (druhé číslo). Vďaka tomu môžeme v prehliadači otvoriť `localhost:5000` a dostať sa k aplikácii v kontajneri.

## Alternatívy 

- **Alternatívy k `app.run()` v produkcii:**
    - V `Dockerfile` sme nechali bežať vývojový server Flasku (`app.run()`). **Toto sa v produkcii nikdy nerobí!** Je pomalý a nebezpečný.
    - V reálnom svete by sme použili produkčný **WSGI server**, napríklad:
        - **Gunicorn:** Veľmi populárny a jednoduchý na použitie.
        - **uWSGI:** Extrémne konfigurovateľný a výkonný.
    - V `Dockerfile` by sme potom zmenili `CMD` napríklad na `CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]`.


## Ako Spustiť Aplikáciu

1.  **Nainštalujte Docker Desktop** z [oficiálnej stránky](https://www.docker.com/products/docker-desktop/).
2.  Otvorte príkazový riadok (terminál) v tomto priečinku (`section-1`).
3.  Spustite príkaz:
    ```bash
    docker-compose up --build
    ```
    - `--build` zabezpečí, že sa obraz vždy postaví nanovo, ak sa zmenil `Dockerfile`.
4.  Otvorte webový prehliadač a prejdite na adresu [http://localhost:5000](http://localhost:5000).

Ak chcete aplikáciu zastaviť, v termináli stlačte `CTRL+C`.