## Role 1: Vykreslování mapy a ukazatelů
- Vytvoř si soubor *mapa_test.py*.

- Zobraz mapu vycentrovanou na Olomouc pomocí folium a streamlit-folium.

- Vytvoř kód, který na mapě nakreslí velký kruh (folium.Circle) s poloměrem x metrů (kde x = cca 15 minut chůze) kolem nějakého testovacího bodu (např. Hejčín).

- Přidej kód, který vezme seznam souřadnic od Role 2 (např. supermarkety) a vykreslí je jako malé tečky na mapě.

- Vykreslené obchody kategorizuj jako "obchod" a přiřaď jim konkrétní barvu.

## Role 2: Práce s daty, vzorec pro výpočet indexu žití
- Vytvoř si soubor *vypocet_test.py* a importuj knihovnu geopy.distance.

- Napiš funkci spocitej_vzdalenost(bod_A, bod_B), která vezme dvoje GPS souřadnice a vrátí vzdálenost v metrech.

- Vytvoř v Pythonu cvičný seznam souřadnic všech Lidlů v Olomouci.

- Napiš funkci, která vezme tvou testovací adresu a zjistí, kolik z těchto obchodů je v okruhu (viz. Role 1).

- V průběhu přemýšlej nad vzorcem, který by hodnotil dle vaší škály kvalitu života v zadané oblasti podle výskytu různých bodů zájmu.

## Role 3: Vedení, design, prezentace
- Jdi na web [Overpass Turbo](https://overpass-turbo.eu/), najdi na mapě Olomouc a pomocí tlačítka *Průvodce* vyhledej "supermarket". Data vyexportuj jako GeoJSON nebo list souřadnic. Tyto data pak předáš Roli 2.

- V hlavním souboru *app.py* vytvoř uživatelské rozhraní: Použij st.slider, aby si uživatel mohl nastavit, jak moc je pro něj důležitá škola, obchody, zeleň,...(0-100 %)

- Pomocí st.metric vykresli číslo, které bude ukazovat výsledný "Index žití" (zatím tam dej nějaké číslo natvrdo).

- Založ prezentaci: 1. Název týmu a logo, 2. Jaký problém řešíme, 3. Naše řešení.