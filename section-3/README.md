# Section 3 / Task A - Thought Process: Production Went Down

### Môj Vyšetrovací a Riešiteľský Proces

### Fáza 1: Okamžitá Reakcia a Obnova Služby (Prvých 5-15 minút)

V tejto fáze je **absolútnou prioritou obnoviť funkčnosť služby pre zákazníkov**. Analýza príčiny je sekundárna.

**Krok 1: Zachovať pokoj a začať komunikovať.**
-   **Akcia:** Okamžite založím komunikačný kanál pre incident (napr. dedikovaný Slack kanál, "war room" v MS Teams).
-   **Dôvod:** Transparentná a centralizovaná komunikácia je kľúčová. Zabraňuje chaosu, duplicitnej práci a informuje všetky zainteresované strany (manažment, podpora, ďalší inžinieri) o aktuálnom stave. Prvá správa je jednoduchá: *"Potvrdzujem výpadok nasadenej apky. Všetku komunikáciu prosím smerujte sem"*

**Krok 2: Overiť a definovať rozsah problému.**
-   **Akcia:** Rýchlo si overím, či je výpadok reálny a aký má dopad. Použijem rozne zariadenia.
    -   Je "dole" celá aplikácia, alebo len jedna jej časť (napr. prihlásenie, nákupný košík)?
    -   Je problém geograficky ohraničený, VPN? (Použijem nástroje ako `downforeveryoneorjustme.com` alebo interné syntetické monitoringy).
    -   Je to problém pre všetkých používateľov alebo len pre určitú skupinu?
-   **Dôvod:** Presné definovanie problému mi pomôže zamerať sa na správnu časť systému. "Je to dole" je príliš vágne.

**Krok 3: Skontrolovať kľúčové dashboardy (prvých 60 sekúnd pohľadu).**
-   **Akcia:** Otvorím si hlavný monitorovací dashboard. Hľadám zjavné anomálie, ktoré sa časovo zhodujú so začiatkom výpadku:
    -   **Traffic:** Poklesol počet požiadaviek na nulu?
    -   **Error Rate:** Vystrelil počet chýb (HTTP 5xx) na 100%?
    -   **Latency:** Zvýšila sa latencia na neúnosnú úroveň?
    -   **Zdroje:** Je niektorá služba preťažená (CPU, RAM na 100%)? Sú plné disky?

**Krok 4: Skontrolovať nedávne zmeny.**
-   **Akcia:** Spýtam sa v komunikačnom kanáli: *"Bolo v poslednej hodine nasadené niečo nové? Zmena kódu, infraštruktúry (Terraform), konfigurácie, feature flag?"* Súčasne kontrolujem Git históriu hlavnej vetvy a záznamy z CI/CD pipeline.
-   **Dôvod:** **Väčšina výpadkov je spôsobená zmenou.** Ak bola nedávno nasadená nová verzia, najrýchlejším riešením je takmer vždy okamžitý **rollback** na predchádzajúcu, stabilnú verziu. Tým obnovím službu a získam čas na analýzu problému v offline prostredí.

**Krok 5: Vyhlásiť riešenie alebo pokračovať v hlbšej analýze.**
-   **Scenár A (Rollback):** Ak bola identifikovaná chybná zmena, spustím proces rollbacku. Komunikujem: *"Identifikovali sme pravdepodobnú príčinu v poslednom nasadení. Spúšťam rollback. Očakávaná obnova služby do 5 minút."*
-   **Scenár B (Neznáma príčina):** Ak nie je zrejmá žiadna nedávna zmena, problém je pravdepodobne v samotnej infraštruktúre alebo externých závislostiach. Prechádzam do Fázy 2.

---

### Fáza 2: Hĺbková Analýza a Identifikácia Príčiny

Ak rýchle kroky neviedli k riešeniu, začínam systematicky analyzovať systém "zhora nadol".

**Krok 6: Sledovať cestu požiadavky.**
-   **Akcia:** Prejdem si v hlave (alebo podľa diagramu architektúry) celú cestu, ktorou prechádza požiadavka od používateľa až po dáta. Na každom kroku kontrolujem logy a metriky.
    1.  **DNS & CDN:** Funguje preklad domény? Nie je problém v CDN (napr. Cloudflare)?
    2.  **Load Balancer (LB):** Sú `health checks` pre backendy v poriadku? Vidí LB nejaké zdravé ciele (targety)? Skontrolujem logy LB.
    3.  **Frontend/API Gateway:** Sú pody tejto služby v stave `Running`? Nie sú v `CrashLoopBackOff`? Skontrolujem logy, či nehlásia chyby pri spojení s backendom.
    4.  **Backend Služby:** To isté ako pri bode 3. Skontrolujem logy aplikácie – hľadám chybové hlášky, stack tracy.
    5.  **Databáza / Cache:** Je databáza dostupná? Nie je preťažená (vysoké CPU, málo voľných spojení)? Skontrolujem logy pomalých dopytov (slow query log).
    6.  **Externé Služby:** Nezlyháva nejaká externá API, od ktorej závisíme (napr. platobná brána, emailový servis)?

**Krok 7: Eskalácia (ak je to potrebné).**
-   **Akcia:** Ak narazím na problém, ktorý presahuje moje znalosti (napr. komplexný problém s databázou), neváham a privolám špecialistu (napr. databázového administrátora, senior vývojára).

---

### Fáza 3: Post-incidentné Kroky a Prevencia

Keď je služba obnovená, práca sa nekončí.

**Krok 8: Potvrdenie obnovy a ukončenie komunikácie.**
-   **Akcia:** Overím, že systém je plne funkčný a stabilný. V komunikačnom kanáli oznámim: *"Služba bola plne obnovená o [čas]. Budeme pokračovať v monitorovaní. Ďakujem všetkým za pomoc. Príčinu budeme analyzovať a pripravíme post-mortem report."*

**Krok 9: Naplánovanie stretnutia.**
-   **Akcia:** Zorganizujem stretnutie so všetkými zúčastnenými. Cieľom **nie je hľadať vinníka**, ale poučiť sa z chyby.

**Krok 10: Vytvorenie Reportu.**
-   **Akcia:** Spíšem dokument, ktorý obsahuje:
    -   **Časovú os incidentu:** Kedy sa začal, kedy bol detekovaný, kedy bol vyriešený.
    -   **Dopad:** Čo presne nefungovalo a koľkých používateľov to ovplyvnilo.
    -   **Root Cause Analysis (RCA):** Podrobný popis, prečo k chybe došlo (napr. "Nedostatočné testovanie novej knižnice viedlo k memory leaku pod vysokou záťažou.").
    -   **Akčné kroky (Action Items):** Zoznam konkrétnych úloh s pridelenými vlastníkmi a termínmi, ktoré zabránia opakovaniu problému. Príklady:
        -   *"Pridať do CI pipeline záťažové testy pre pamäťovú náročnosť."*
        -   *"Vylepšiť monitoring databázy o alert na počet aktívnych spojení."*
        -   *"Vytvoriť automatizovaný rollback skript."*
