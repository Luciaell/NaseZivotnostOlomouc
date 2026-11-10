1. Zaregistruj se na OpenRouteService a získej zdarma API klíč.
2. Vytvoř nový soubor s názvem *.env*, ten otevři a do něj vytvoř proměnnou ORS_API_KLIC, do které uložíš tvůj API klíč ve formátu string.
    - (do .env se ukládají tzv. environmental variables ve formátu KLÍČ="hodnota". Jde i o API klíče, které se rozhodně nesdílejí a nikam nenahrávají! Kdyby šlo o placené API klíče, poskytli byste celému internetu vaše peníze.
3. Vytvoř si ve složce projektu virutální prostředí (*py -m venv venv*).)
    - (virtuální prostředí oddělí moduly, které stahujeme a instalujeme od zbystku projektů, abychom si postupně nenadělali v počítači nepořádek.)
4. Vytvoř si ve složce projektu soubor s názvem *.gitignore*. Do něj napiš (každé na nový řádek):
    venv/
    .env
    - (.gitignore vypisuje, které soubory má Git ignorovat - nesledovat a nenahrávat je. .env z dříve uvedených důvodů, venv z důvodů toho, že obsahuje spousty souborů, kterými si nechceme špinit GitHub repozitář a které jsou specifické pro lokální instalaci pythonu a tím pádem je nechceme přenášet na jiný počítač.)
5. Pomocí *py -m pip install -r requirements.txt* hromadně nainstaluj veškeré moduly vypsané v souboru requirements.txt.