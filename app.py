def pozdrav():
    print("Ahoj Zebry!")
#následující kód se spustí pouze pokud je tento soubor spuštěn jako hlavní program
#až budete načítat ostatní soubory pomocí import, je třeba také použít if __name__ == "__main__":, aby se zabránilo spuštění celého obsahu souboru při importu
if __name__ == "__main__":
    pozdrav()