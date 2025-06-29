# Section 2 / Task A - Troubleshooting: 502 Bad Gateway

### ● Identifikácia Príčiny Chyby (Root Cause Analysis)

Chyba `502 Bad Gateway` je HTTP status kód, ktorý znamená, že jeden server na internete (v našom prípade Nginx) prijal neplatnú odpoveď od iného servera, ku ktorému pristupoval (v našom prípade Node.js aplikácia). V kontexte našej zostavy to znamená, že Nginx sa nedokázal úspešne spojiť s backendovou službou `web`.

Po preskúmaní poskytnutých konfiguračných súborov bol problém identifikovaný ako **nezhoda v konfigurovaných sieťových portoch** medzi týmito dvoma službami.

1.  **Konfigurácia Nginx (`nginx.conf`)**:
    Nginx bol nakonfigurovaný tak, aby preposielal všetky prichádzajúce požiadavky na službu `web` na port `8080`.
    ```nginx
    # nginx.conf
    location / {
        proxy_pass http://web:8080;
    }
    ```

2.  **Konfigurácia Node.js Aplikácie (`server.js`)**:
    Aplikácia bola naprogramovaná tak, aby počúvala na požiadavky na porte `3000`.
    ```javascript
    // server.js
    const PORT = 3000;
    app.listen(PORT, () => {
        console.log(`Server is running on port ${PORT}`);
    });
    ```

**Záver:** Príčinou chyby je, že Nginx posiela sieťovú prevádzku na port, na ktorom Node.js aplikácia nepočúva (`8080` namiesto `3000`). Spojenie teda zlyhá a Nginx vráti klientovi chybu 502.

---
### ● Aplikovanie Opravy (Fix Implementation)

Riešenie spočíva v zosúladení portov tak, aby Nginx posielal požiadavky na správny port, na ktorom Node.js aplikácia beží. Oprava bola vykonaná úpravou konfiguračného súboru `nginx.conf`.

**Opravená `nginx.conf`:**
```nginx
server {
    listen 80;

    location / {
        # OPRAVA: Port bol zmenený z 8080 na 3000, aby zodpovedal
        # portu, na ktorom beží backendová Node.js aplikácia.
        proxy_pass http://web:3000;
    }
}
```
Touto jednoduchou zmenou Nginx teraz správne smeruje požiadavky na port `3000` služby `web`, čím sa obnoví funkčná komunikácia a chyba 502 je odstránená.

---
### ● Vysvetlenie, ako Predchádzať Problému v Produkcii (Production Prevention)

Manuálne konfiguračné chyby sú častou príčinou výpadkov. Aby sme minimalizovali ich riziko v produkčnom prostredí, je kľúčové zaviesť automatizáciu a osvedčené postupy (best practices).

1.  **Centralizovaná Konfigurácia pomocou Environmentálnych Premenných**
    Namiesto pevne zakódovaných hodnôt (tzv. "hardcoding") by sa mali kritické parametre, ako sú porty, definovať ako environmentálne premenné. Tieto premenné sa nastavia na jednom mieste (napr. v `docker-compose.yml` alebo v systéme pre správu secretov) a všetky služby ich odtiaľ načítajú.

    *   **Výhody:** Znižuje sa riziko preklepov a nekonzistencií. Zmena portu si vyžaduje úpravu len na jednom mieste.
    *   **Príklad implementácie:**
        ```yaml
        # V docker-compose.yml
        services:
          web:
            environment:
              - PORT=3000
        ```
        ```javascript
        // V server.js
        const PORT = process.env.PORT || 3000;
        ```
        Pre Nginx sa dá použiť nástroj ako `envsubst`, ktorý pri štarte kontajnera nahradí premenné v šablóne konfiguračného súboru.

2.  **Automatizované Integračné Testy v CI/CD Pipeline**
    Pred každým nasadením do produkcie by mala byť spustená automatizovaná CI/CD pipeline, ktorá obsahuje integračné testy. Tieto testy postavia celú aplikáciu v izolovanom prostredí (presne ako je definovaná v `docker-compose.yml`) a overia základnú funkčnosť.

    *   **Príklad testu:** Jednoduchý `curl` príkaz na endpoint Nginx.
      ```bash
      # Príklad testovacieho skriptu v CI/CD
      docker-compose up -d --build
      sleep 5 # Počkáme, kým sa služby naštartujú
      if curl --fail http://localhost/; then
          echo "Integration test passed!"
      else
          echo "Integration test failed! 502 error detected."
          exit 1
      fi
      ```
    *   Ak test zlyhá (napr. vráti kód 502), pipeline sa preruší a chybná verzia sa nikdy nedostane k používateľom.

3.  **Implementácia Health Checks a Readiness Probes**
    V moderných Kubernetes je štandardom definovať `health checks`.
    *   **Readiness Probe:** Kontroluje, či je aplikácia pripravená prijímať prevádzku. Ak by Nginx nevedel komunikovať s backendom, sonda by zlyhala a orchestrátor by na Nginx neposielal žiadne požiadavky, kým sa problém nevyrieši. Tým sa chyba izoluje a neovplyvní používateľov.
    *   **Liveness Probe:** Kontroluje, či aplikácia stále beží správne. Ak nie, orchestrátor ju automaticky reštartuje.
