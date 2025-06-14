# Betclic Live Scraper

Ten projekt umożliwia automatyczne pobieranie danych o meczach na żywo z serwisu Betclic.pl, zapisując je do lokalnej bazy SQLite.

## Spis treści

* [Opis](#opis)
* [Wymagania](#wymagania)
* [Instalacja](#instalacja)
* [Pliki w projekcie](#pliki-w-projekcie)
* [Użycie](#użycie)
* [Schemat bazy danych](#schemat-bazy-danych)
* [Konfiguracja](#konfiguracja)
* [Testowanie bazy](#testowanie-bazy)
* [Licencja](#licencja)

## Opis

Skrypt `main.py` (lub `ee690924-d173-4128-bc20-595123abe72d.py`) wykorzystuje bibliotekę [undetected\_chromedriver](https://pypi.org/project/undetected-chromedriver/) oraz Selenium do:

* Automatycznego otwierania i obsługi przeglądarki Chrome z ukrytym profilem.
* Dynamicznego przewijania strony Betclic Live.
* Blokowania aktualizacji (fetch/XHR) przed zrzutem zawartości.
* Pobierania informacji o meczach (nazwa, sport, drużyny, czas, wynik, kursy).
* Zapisania danych do lokalnej bazy SQLite `matches.db`.

## Wymagania

* Python 3.8+ w ścieżce systemowej (`python` w `%PATH%`).
* System Windows (do ukrywania okna i użycia `pywin32`, `win32gui`, `win32con`).

## Instalacja

1. Sklonuj repozytorium:

   ```bash
   git clone https://github.com/Mantiee/betclic-live-scraper.git
   cd betclic-live-scraper

   ```
   
2. Uruchom `installer.bat`, aby zainstalować wszystkie pakiety:
```bat
installer.bat
```

* Aktualizuje `pip`.
* Instaluje: `undetected-chromedriver`, `selenium`, `pywin32`.

## Pliki w projekcie

* `main.py` – główny skrypt do scrapowania.
* `installer.bat` – instalator zależności.
* `run_main.bat` – uruchamia `main.py`.
* `show_db.bat` – uruchamia `test_the_db.py` do przeglądu bazy.
* `test_the_db.py` – przykładowy skrypt wyświetlający zawartość `matches.db`.
* `chrome_profile/` – folder profilu Chrome (tworzony automatycznie).
* `matches.db` – plik bazy danych SQLite (tworzony automatycznie).

## Użycie

1. Uruchom scraper:

   ```bat
   ```

run\_main.bat

````
2. Po zatrzymaniu (Ctrl+C) lub w dowolnym momencie, podejrzyj zebrane dane:
```bat
show_db.bat
````

## Schemat bazy danych

Tabela `matches`:

| Kolumna                           | Typ     | Opis                              |
| --------------------------------- | ------- | --------------------------------- |
| `id`                              | INTEGER | Klucz główny, auto-increment      |
| `current_global_time`             | TEXT    | Znacznik czasu pobrania           |
| `match_name`                      | TEXT    | Pełna nazwa meczu                 |
| `sport_type`                      | TEXT    | Nazwa sportu (ikonka)             |
| `left_player`                     | TEXT    | Lewa drużyna/gracz                |
| `right_player`                    | TEXT    | Prawa drużyna/gracz               |
| `match_time`                      | TEXT    | Aktualny czas meczu (timer)       |
| `left_player_score`               | TEXT    | Wynik lewego zespołu/gracza       |
| `right_player_score`              | TEXT    | Wynik prawego zespołu/gracza      |
| `sets_top_player`                 | TEXT    | Wyniki zakończonych setów (góra)  |
| `set_current_score_top_player`    | TEXT    | Wynik bieżącego seta (góra)       |
| `set_subscore_top_player`         | TEXT    | Podwynik (góra)                   |
| `sets_bottom_player`              | TEXT    | Wyniki zakończonych setów (dół)   |
| `set_current_score_bottom_player` | TEXT    | Wynik bieżącego seta (dół)        |
| `set_subscore_bottom_player`      | TEXT    | Podwynik (dół)                    |
| `left_odds`                       | TEXT    | Kurs na lewego zawodnika/wygraną  |
| `middle_odds`                     | TEXT    | Kurs środkowy (typy 3-way)        |
| `right_odds`                      | TEXT    | Kurs na prawego zawodnika/wygraną |

## Konfiguracja

* Zmienna `HIDE_CHROME_WINDOW` w kodzie (`main.py`) umożliwia ukrycie okna przeglądarki.
* Folder profilu Chrome można czyścić lub zmieniać (`chrome_profile/`).

## Testowanie bazy

W pliku `test_the_db.py` możesz zaimplementować prosty skrypt w Pythonie, np.:

```python
import sqlite3
conn = sqlite3.connect('matches.db')
for row in conn.execute('SELECT * FROM matches ORDER BY id DESC LIMIT 10'):
    print(row)
conn.close()
```

Uruchom go przez:

```bat
show_db.bat
```

## Licencja

[MIT](LICENSE)

---
