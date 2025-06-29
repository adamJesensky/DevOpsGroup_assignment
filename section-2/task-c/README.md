# Section 2 / Task C - Troubleshooting: Docker Build Fails (no space left on device)

### ● Diagnostika Problému s Plným Diskom v CI (CI Disk Full Issue Diagnosis)

Chyba `no space left on device` počas `docker build` signalizuje, že na stroji, kde build beží (typicky dočasný "runner" alebo "agent" v CI/CD systéme), sa minul dostupný diskový priestor.

Pri analýze poskytnutého `Dockerfile` môžeme identifikovať niekoľko zdrojov nadmernej spotreby miesta:

**Poskytnutý `Dockerfile`:**
```dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y nodejs npm
COPY . /app
WORKDIR /app
RUN npm install
CMD ["node", "index.js"]
```

**Hlavné príčiny problému:**

1.  **Veľký základný image (`ubuntu:20.04`):**
    Plná verzia Ubuntu je veľký image, ktorý obsahuje množstvo nástrojov a knižníc, ktoré finálna Node.js aplikácia nepotrebuje. Už samotný základný image môže zaberať stovky MB.

2.  **Nečistenie `apt` cache:**
    Príkaz `apt-get update` sťahuje zoznamy balíčkov a ukladá ich do cache. Po inštalácii (`apt-get install`) tieto zoznamy zostávajú na disku ako nepotrebný balast. V kontexte jednorazového buildu sú úplne zbytočné.

3.  **Kopírovanie nepotrebných súborov (`COPY . /app`):**
    Tento príkaz skopíruje **všetko** z aktuálneho adresára projektu do Docker image. To často zahŕňa:
    *   Adresár `node_modules` (ak bol spustený `npm install` lokálne).
    *   Adresár `.git`, ktorý môže byť veľmi veľký.
    *   Dočasné súbory, logy, dokumentáciu a iné artefakty, ktoré nie sú potrebné pre beh aplikácie.

4.  **Ukladanie buildovacích závislostí vo finálnom image:**
    Príkaz `npm install` inštaluje všetky závislosti, vrátane `devDependencies` (napr. testovacie knižnice, lintery), ktoré sú potrebné len na build, nie na beh aplikácie. Tieto zbytočne zväčšujú finálny image.
---

### ● Návrh Dočasných a Permanentných Riešení (Temporary and Permanent Fixes)

#### Dočasné (Okamžité) Riešenia

Tieto kroky môžu rýchlo uvoľniť miesto na CI runneri a umožniť úspešné dokončenie buildu, ale neriešia koreňovú príčinu problému.

1.  **Vyčistenie disku CI runnera:**
    Väčšina CI/CD systémov umožňuje spustiť skript na vyčistenie pred samotným buildom. Príkaz `docker system prune -af` odstráni všetky nepoužívané kontajnery, siete, image a build cache.
    ```bash
    # Príklad kroku v CI/CD pipeline
    - name: Clean up Docker resources
      run: docker system prune -af
    ```

2.  **Zväčšenie diskového priestoru runnera:**
    Ak to platforma umožňuje, dočasné zväčšenie disku pre CI runnerov (napr. z 20 GB na 50 GB) problém "kúpi čas", ale je to neekonomické a neudržateľné riešenie.

#### Permanentné (Odporúčané) Riešenia

Tieto riešenia sú zamerané na optimalizáciu `Dockerfile` podľa osvedčených postupov (best practices), čo vedie k menším, rýchlejším a bezpečnejším image.

1.  **Použitie `.dockerignore` súboru:**
    Vytvorte v koreňovom adresári projektu súbor `.dockerignore`. Tento súbor funguje rovnako ako `.gitignore` a zabráni príkazu `COPY` kopírovať nepotrebné súbory do image.
    ```
    # .dockerignore
    .git
    node_modules
    npm-debug.log
    Dockerfile
    .dockerignore
    README.md
    ```

2.  **Optimalizácia `Dockerfile` pomocou Multi-Stage Buildu:**
    Toto je najdôležitejšia a najefektívnejšia technika. Build sa rozdelí na viacero fáz.
    *   **Fáza 1 (`builder`):** Použije sa väčší image s buildovacími nástrojmi. Nainštalujú sa všetky závislosti (vrátane `devDependencies`) a postaví sa produkčná verzia aplikácie.
    *   **Fáza 2 (finálna):** Použije sa minimalistický "distroless" alebo "alpine" image. Z `builder` fázy sa skopírujú **iba nevyhnutné artefakty** (napr. adresár `node_modules` a kód aplikácie).

**Optimalizovaný `Dockerfile`:**
```dockerfile
# --- Fáza 1: Builder ---
# Použijeme oficiálny Node.js image, ktorý obsahuje všetky nástroje na build
FROM node:16 as builder

WORKDIR /app

# Najprv skopírujeme len package.json, aby sme využili Docker cache
COPY package*.json ./
# Nainštalujeme všetky závislosti vrátane devDependencies pre build a testy
RUN npm install

# Skopírujeme zvyšok kódu
COPY . .

# (Voliteľné) Tu môže bežať build krok, napr. pre TypeScript alebo React
# RUN npm run build

# --- Fáza 2: Finálny produkčný image ---
# Použijeme menší, odľahčený image pre produkciu
FROM node:16-alpine

WORKDIR /app

# Skopírujeme závislosti z builder fázy
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
# Skopírujeme iba kód aplikácie
COPY --from=builder /app/index.js ./index.js

# Nastavíme používateľa s menšími oprávneniami (bezpečnostné best practice)
USER node

CMD ["node", "index.js"]
```
---

### ● Definovanie Monitorovacích Opatrení (Monitoring Measures)

Prevencia je lepšia ako náprava. Aby sme predišli budúcim problémom s diskovým priestorom, mali by sme implementovať nasledujúce monitorovacie opatrenia:

1.  **Monitorovanie Využitia Disku na CI Runneroch:**
    Nastavte alerting v monitorovacom systéme (napr. Prometheus/Grafana, Datadog), ktorý vás upozorní, ak využitie disku na CI runneroch prekročí určitú hranicu (napr. 80%). To vám dá čas reagovať skôr, ako dôjde k úplnému zaplneniu.

2.  **Sledovanie Veľkosti Docker Image:**
    Integrujte do CI/CD pipeline krok, ktorý kontroluje veľkosť výsledného Docker image. Ak image prekročí definovaný prah (napr. 500 MB), build zlyhá alebo sa vygeneruje varovanie. To donúti vývojárov udržiavať image optimalizované.
    ```bash
    # Príklad kroku v CI/CD
    - name: Check image size
      run: |
        docker build -t my-app .
        SIZE_MB=$(docker images my-app --format "{{.Size}}" | sed 's/MB//')
        if (( $(echo "$SIZE_MB > 500" | bc -l) )); then
          echo "Error: Image size ($SIZE_MB MB) exceeds the 500MB threshold."
          exit 1
        fi
    ```

3.  **Pravidelné Automatizované Čistenie:**
    Nastavte naplánovanú úlohu (cron job) na CI runneroch, ktorá pravidelne spúšťa `docker system prune -af`. Tým sa zabezpečí, že sa na disku nebudú hromadiť staré a nepoužívané Docker objekty.