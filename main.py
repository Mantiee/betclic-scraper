import undetected_chromedriver as uc
import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import win32gui
import win32con
import sqlite3

HIDE_CHROME_WINDOW = False

# ------------------------------
# KONFIGURACJA PRZEGLĄDARKI
# ------------------------------
profile_path = os.path.join(os.getcwd(), "chrome_profile")
if not os.path.exists(profile_path):
    os.makedirs(profile_path)
    print("Utworzono nowy folder profilu:", profile_path)
else:
    print("Używam istniejącego folderu profilu:", profile_path)

options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-popup-blocking")

prefs = {
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.popups": 2,
}
options.add_experimental_option("prefs", prefs)

driver = uc.Chrome(options=options)


# ------------------------------
# KONFIGURACJA BAZY DANYCH SQLITE
# ------------------------------
def setup_database():
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()

    # Tworzenie tabeli matches z nową strukturą
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_global_time TEXT,
            match_name TEXT,
            sport_type TEXT,
            left_player TEXT,
            right_player TEXT,
            match_time TEXT,
            left_player_score TEXT,
            right_player_score TEXT,
            sets_top_player TEXT,
            set_current_score_top_player TEXT,
            set_subscore_top_player TEXT,
            sets_bottom_player TEXT,
            set_current_score_bottom_player TEXT,
            set_subscore_bottom_player TEXT,
            left_odds TEXT,
            middle_odds TEXT,
            right_odds TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Baza danych i tabela 'matches' zostały skonfigurowane.")

# Wywołanie konfiguracji bazy danych przy starcie
setup_database()

def unblock_page_updates():
    driver.execute_script("""
        // Przywracanie window.fetch
        window.fetch = window.originalFetch || window.fetch;
        delete window.originalFetch;

        // Przywracanie XMLHttpRequest
        window.XMLHttpRequest = window.originalXMLHttpRequest || window.XMLHttpRequest;
        delete window.originalXMLHttpRequest;
    """)
    print("Odblokowano aktualizacje strony.")

def save_to_database(data):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO matches (
            current_global_time, match_name, sport_type, left_player, right_player, match_time,
            left_player_score, right_player_score, sets_top_player, set_current_score_top_player,
            set_subscore_top_player, sets_bottom_player, set_current_score_bottom_player,
            set_subscore_bottom_player, left_odds, middle_odds, right_odds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['current_global_time'], data['match_name'], data['sport_type'], data['left_player'],
        data['right_player'], data['match_time'], data['left_player_score'],
        data['right_player_score'], data['sets_top_player'], data['set_current_score_top_player'], data['set_subscore_top_player'],
        data['sets_bottom_player'], data['set_current_score_bottom_player'], data['set_subscore_bottom_player'],
        data['left_odds'], data['middle_odds'], data['right_odds']
    ))

    conn.commit()
    conn.close()

if HIDE_CHROME_WINDOW:
    hwnd = win32gui.GetForegroundWindow()  # Pobierz uchwyt aktywnego okna
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)  # Ukryj okno

def process_page():
    # ------------------------------
    # ODWIEDZENIE STRONY BETCLIC
    # ------------------------------

    hwnd = win32gui.GetForegroundWindow()  # Pobierz uchwyt aktywnego okna

    driver.get("https://www.betclic.pl/live")
    print("Tytuł strony:", driver.title)

    # Rozpoczęcie timera
    start_time = time.time()
    print(f"Timer rozpoczęty o: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

    # Dajemy Angularowi chwilę na załadowanie treści
    time.sleep(2)

    # ------------------------------
    # Dynamiczne przewijanie na sam dół strony
    # ------------------------------
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.8, 1.2))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("Przewinięto stronę na sam dół.")
    current_polish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # ------------------------------
    # ZATRZYMANIE WSZELKICH AKTUALIZACJI STRONY
    # ------------------------------
    driver.execute_script("""
        // Zachowanie oryginalnych funkcji
        window.originalFetch = window.fetch;
        window.originalXMLHttpRequest = window.XMLHttpRequest;

        // Zatrzymanie window.fetch
        window.fetch = function() {
            console.log('Blocked fetch request');
            return Promise.reject('Network requests disabled');
        };

        // Zatrzymanie XMLHttpRequest
        window.XMLHttpRequest = function() {
            this.open = function() { console.log('Blocked XMLHttpRequest'); };
            this.send = function() {};
        };

        // Zatrzymanie dalszego ładowania strony
        window.stop();
    """)
    print("Zablokowano aktualizacje strony (fetch, XMLHttpRequest, window.stop).")

    # ------------------------------
    # POBIERANIE WSZYSTKICH KATEGORII (bucketów)
    # ------------------------------
    try:
        all_buckets = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "sports-live-event-bucket.accordionList.accordionListScorboard.block")
            )
        )
        print(f"Znaleziono {len(all_buckets)} kategorii")
    except Exception as e:
        print("Nie udało się załadować kategorii:", e)
        return  # Zakończ funkcję, aby przejść do odświeżenia

    # ------------------------------
    # PRZETWARZANIE KAŻDEJ KATEGORII
    # ------------------------------
    for bucket in all_buckets:
        # Sprawdzamy, czy bucket jest aktywny – jeżeli nie, klikamy, aby go rozwinąć
        is_active = "is-active" in bucket.get_attribute("class")
        if not is_active:
            try:
                header = bucket.find_element(By.CSS_SELECTOR, "div.accordionList_header")
                driver.execute_script("arguments[0].click();", header)
                time.sleep(1)  # chwila na rozwinięcie
            except Exception as e:
                print(f"Nie udało się rozwinąć kategorii: {e}")
                continue

        # Pobieramy wszystkie event cards (mecze) w danej kategorii
        try:
            event_cards = bucket.find_elements(By.CSS_SELECTOR, "sports-events-event-card.ng-star-inserted")
            print(f"Znaleziono {len(event_cards)} meczów w tej kategorii")
        except Exception as e:
            print(f"Nie udało się znaleźć meczów w tej kategorii: {e}")
            continue

        # ------------------------------
        # PRZETWARZANIE KAŻDEGO MECZU W KATEGORII
        # ------------------------------
        for card in event_cards:

            # --- Aktualny czas w polsce ---
            print("\nAktualny polski czas:", current_polish_time)

            # --- Nazwa meczu ---
            match_name = ""
            try:
                breadcrumb_items = card.find_elements(By.CSS_SELECTOR, "bcdk-breadcrumb-item")
                match_name_parts = []
                if breadcrumb_items:
                    for item in breadcrumb_items:
                        item_text = driver.execute_script(
                            "return arguments[0].innerText || arguments[0].textContent;", item
                        ).strip()
                        if item_text and "<!--" not in item_text:
                            match_name_parts.append(item_text)
                    match_name = " · ".join(match_name_parts)
                else:
                    labels = card.find_elements(By.CSS_SELECTOR, "span.breadcrumb_itemLabel")
                    for label in labels:
                        label_text = driver.execute_script(
                            "return arguments[0].innerText || arguments[0].textContent;", label
                        ).strip()
                        if label_text and "<!--" not in label_text:
                            match_name_parts.append(label_text)
                    match_name = " · ".join(match_name_parts)
                if not match_name or "<!--" in match_name:
                    breadcrumb_container = card.find_element(By.CSS_SELECTOR, "div.breadcrumb_list")
                    match_name = driver.execute_script("""
                        function extractVisibleText(element) {
                            if (element.nodeType === Node.TEXT_NODE) {
                                return element.textContent.trim();
                            }
                            if (window.getComputedStyle(element).display === 'none') {
                                return '';
                            }
                            let text = '';
                            for (let child of element.childNodes) {
                                if (child.nodeType === Node.TEXT_NODE) {
                                    let content = child.textContent.trim();
                                    if (content && !content.includes('<!--')) {
                                        text += ' ' + content;
                                    }
                                } else if (child.nodeType === Node.ELEMENT_NODE) {
                                    text += ' ' + extractVisibleText(child);
                                }
                            }
                            return text.trim();
                        }
                        return extractVisibleText(arguments[0]);
                    """, breadcrumb_container).strip()
            except Exception as e:
                match_name = f"Brak nazwy meczu (błąd: {str(e)})"

            match_name = match_name.replace('<!---->', '').strip()
            if not match_name:
                match_name = "Nie udało się pobrać nazwy meczu"

            print("Mecz:", match_name)

            # --- Pobieranie nazwy sportu z ikony (tylko do wyświetlenia) ---
            sport_name = "Nieznany"
            try:
                sport_icon = card.find_element(By.CSS_SELECTOR, "span.breadcrumb_itemIcon.icons[class*='icon_sport_']")
                class_list = sport_icon.get_attribute("class").split()
                for class_name in class_list:
                    if class_name.startswith("icon_sport_"):
                        sport_name = class_name.replace("icon_sport_", "").strip()
                        break
            except Exception as e:
                print(f"Nie udało się pobrać nazwy sportu z ikony: {e}")
            print("Sport:", sport_name)

            # --- Pobieranie nazw drużyn/graczy ---
            left_team = "Brak lewego zespołu/gracza"
            right_team = "Brak prawego zespołu/gracza"
            try:
                # Próbujemy najpierw selektor dla sportów zespołowych (np. piłka nożna)
                left_team_el = card.find_elements(By.CSS_SELECTOR, "div[data-qa='contestant-1-label']")
                if left_team_el:
                    left_team = left_team_el[0].text.strip() or driver.execute_script(
                        "return arguments[0].textContent;",
                        left_team_el[0]).strip()
                else:
                    # Jeśli nie znaleziono, próbujemy selektor dla sportów indywidualnych (np. tenis)
                    left_team_el = card.find_element(By.CSS_SELECTOR,
                                                     "span.scoreboard_contestantLabel[data-qa='contestant-1-label']")
                    left_team = left_team_el.text.strip() or driver.execute_script("return arguments[0].textContent;",
                                                                                   left_team_el).strip()

                right_team_el = card.find_elements(By.CSS_SELECTOR, "div[data-qa='contestant-2-label']")
                if right_team_el:
                    right_team = right_team_el[0].text.strip() or driver.execute_script(
                        "return arguments[0].textContent;",
                        right_team_el[0]).strip()
                else:
                    right_team_el = card.find_element(By.CSS_SELECTOR,
                                                      "span.scoreboard_contestantLabel[data-qa='contestant-2-label']")
                    right_team = right_team_el.text.strip() or driver.execute_script("return arguments[0].textContent;",
                                                                                     right_team_el).strip()
            except Exception as e:
                print(f"Błąd podczas pobierania nazw drużyn/graczy: {e}")

            print("Drużyna/Gracz lewy:", left_team)
            print("Drużyna/Gracz prawy:", right_team)

            # --- Uniwersalne pobieranie czasu meczu ---
            match_time = "Brak informacji o czasie"
            try:
                info_time_divs = card.find_elements(By.CSS_SELECTOR, "div.event_infoTime")
                if info_time_divs:
                    for info_div in info_time_divs:
                        timer_elements = info_div.find_elements(By.CSS_SELECTOR, "scoreboards-timer")
                        if timer_elements:
                            timer_text = timer_elements[0].text.strip() or driver.execute_script(
                                "return arguments[0].textContent;", timer_elements[0]).strip()
                            if timer_text:
                                match_time = timer_text
                                break

                if match_time == "Brak informacji o czasie":
                    timer_elements = card.find_elements(By.CSS_SELECTOR, "scoreboards-timer")
                    if timer_elements:
                        for timer_el in timer_elements:
                            timer_text = timer_el.text.strip() or driver.execute_script(
                                "return arguments[0].textContent;", timer_el).strip()
                            if timer_text:
                                match_time = timer_text
                                break

                if match_time == "Brak informacji o czasie":
                    time_elements = card.find_elements(By.CSS_SELECTOR, "div.scoreboard_periodLabel")
                    if time_elements:
                        time_text = time_elements[0].text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", time_elements[0]).strip()
                        if time_text:
                            match_time = time_text
            except Exception as e:
                match_time = f"Brak informacji o czasie (błąd: {e})"

            print("Czas meczu:", match_time)

            # --- Dynamiczne pobieranie wyników na podstawie struktury ---
            # Inicjalizacja zmiennych
            left_score = None
            right_score = None
            top_subscore = ""
            bottom_subscore = ""
            top_set_current_score = ""
            bottom_set_current_score = ""
            top_set_scores = []
            bottom_set_scores = []

            # 1. Sprawdzamy, czy są globalne wyniki (np. piłka nożna, baseball)
            try:
                score_elements = card.find_elements(By.CSS_SELECTOR, "scoreboards-scoreboard-global-scores")
                if score_elements:
                    left_score_elements = score_elements[0].find_elements(
                        By.CSS_SELECTOR, "span[class*='scoreboard_score scoreboard_score-1']"
                    )
                    if left_score_elements:
                        left_score = left_score_elements[0].text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", left_score_elements[0]
                        ).strip()
                        left_score = left_score.replace('<!---->', '').strip()

                    right_score_elements = score_elements[0].find_elements(
                        By.CSS_SELECTOR, "span[class*='scoreboard_score scoreboard_score-2']"
                    )
                    if right_score_elements:
                        right_score = right_score_elements[0].text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", right_score_elements[0]
                        ).strip()
                        right_score = right_score.replace('<!---->', '').strip()
            except Exception as e:
                print(f"Błąd podczas pobierania wyników globalnych: {e}")

            # 2. Sprawdzamy, czy są sety/SubScore/SetCurrentScore (np. tenis, siatkówka)
            if left_score is None and right_score is None:  # Jeśli nie ma globalnych wyników
                # Pobieramy SubScore (is-currentScore)
                try:
                    current_score_elements = card.find_elements(By.CSS_SELECTOR,
                                                                "div.scoreboard_tableCol.is-currentScore")
                    if len(current_score_elements) >= 2:
                        top_subscore_el = current_score_elements[0].find_element(By.CSS_SELECTOR,
                                                                                 "span.scoreboard_tableCell")
                        top_subscore = top_subscore_el.text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", top_subscore_el).strip()

                        bottom_subscore_el = current_score_elements[1].find_element(By.CSS_SELECTOR,
                                                                                    "span.scoreboard_tableCell")
                        bottom_subscore = bottom_subscore_el.text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", bottom_subscore_el).strip()
                except Exception as e:
                    print(f"Błąd podczas pobierania SubScore: {e}")

                # Pobieramy SetCurrentScore (is-currentPeriodScore)
                try:
                    current_period_elements = card.find_elements(By.CSS_SELECTOR,
                                                                 "div.scoreboard_tableCol.is-currentPeriodScore")
                    if len(current_period_elements) >= 2:
                        top_set_current_el = current_period_elements[0].find_element(By.CSS_SELECTOR,
                                                                                     "span.scoreboard_tableCell")
                        top_set_current_score = top_set_current_el.text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", top_set_current_el).strip()

                        bottom_set_current_el = current_period_elements[1].find_element(By.CSS_SELECTOR,
                                                                                        "span.scoreboard_tableCell")
                        bottom_set_current_score = bottom_set_current_el.text.strip() or driver.execute_script(
                            "return arguments[0].textContent;", bottom_set_current_el).strip()
                except Exception as e:
                    print(f"Błąd podczas pobierania SetCurrentScore: {e}")

                # Pobieramy wyniki zakończonych setów (pomijamy te z is-currentScore i is-currentPeriodScore)
                try:
                    period_rows = card.find_elements(By.CSS_SELECTOR,
                                                     "scoreboards-scoreboard-periods-scores.scoreboard_tableRow")
                    if len(period_rows) >= 2:
                        # Pierwszy wiersz – sety dla gracza top
                        top_set_cells = period_rows[0].find_elements(By.CSS_SELECTOR, "span.scoreboard_tableCell")
                        for cell in top_set_cells:
                            cell_text = cell.text.strip()
                            # Sprawdzamy, czy komórka należy do is-currentScore lub is-currentPeriodScore
                            parent_col = cell.find_element(By.XPATH, "./parent::div")
                            parent_classes = parent_col.get_attribute("class")
                            if (cell_text and (
                                    cell_text == "A" or cell_text.replace(',', '').replace('.', '').isdigit()) and
                                    "is-currentScore" not in parent_classes and "is-currentPeriodScore" not in parent_classes):
                                top_set_scores.append(cell_text)

                        # Drugi wiersz – sety dla gracza bottom
                        bottom_set_cells = period_rows[1].find_elements(By.CSS_SELECTOR, "span.scoreboard_tableCell")
                        for cell in bottom_set_cells:
                            cell_text = cell.text.strip()
                            # Sprawdzamy, czy komórka należy do is-currentScore lub is-currentPeriodScore
                            parent_col = cell.find_element(By.XPATH, "./parent::div")
                            parent_classes = parent_col.get_attribute("class")
                            if (cell_text and (
                                    cell_text == "A" or cell_text.replace(',', '').replace('.', '').isdigit()) and
                                    "is-currentScore" not in parent_classes and "is-currentPeriodScore" not in parent_classes):
                                bottom_set_scores.append(cell_text)
                except Exception as e:
                    top_set_scores, bottom_set_scores = [], []
                    print(f"Błąd podczas pobierania setów: {e}")

            # Wyświetlanie wyników
            if left_score is not None and right_score is not None:
                print(f"Wynik {left_team}: {left_score}")
                print(f"Wynik {right_team}: {right_score}")
            else:
                if top_set_scores or top_set_current_score or top_subscore:
                    set_info = " | ".join(top_set_scores) if top_set_scores else ""
                    output = f"{left_team}"
                    if set_info:
                        output += f" | Sety: {set_info}"
                    if top_set_current_score:
                        output += f" | SetCurrentScore: {top_set_current_score}"
                    if top_subscore:
                        output += f" | SubScore: {top_subscore}"
                    print(output)
                else:
                    print(f"{left_team} | Brak wyników")

                if bottom_set_scores or bottom_set_current_score or bottom_subscore:
                    set_info = " | ".join(bottom_set_scores) if bottom_set_scores else ""
                    output = f"{right_team}"
                    if set_info:
                        output += f" | Sety: {set_info}"
                    if bottom_set_current_score:
                        output += f" | SetCurrentScore: {bottom_set_current_score}"
                    if bottom_subscore:
                        output += f" | SubScore: {bottom_subscore}"
                    print(output)
                else:
                    print(f"{right_team} | Brak wyników")

            # --- Pobieranie przycisków z kursami ---
            odds_list = []
            left_odds = None
            middle_odds = None
            right_odds = None
            try:
                odds_buttons = card.find_elements(By.CSS_SELECTOR,
                                                  "button.btn.is-odd.is-large, button.btn.is-odd.is-large.ng-star-inserted, button.btn.is-odd.is-large.is-strikethrough.is-disabled")
                for idx, button in enumerate(odds_buttons):
                    player_name = ""
                    try:
                        full_text = ""
                        ellipsis_spans = button.find_elements(By.CSS_SELECTOR, "span.ellipsis")
                        if ellipsis_spans:
                            ellipsis_text = ellipsis_spans[0].text.strip() or driver.execute_script(
                                "return arguments[0].textContent;", ellipsis_spans[0]).strip()
                            full_text += ellipsis_text

                        clip_spans = button.find_elements(By.CSS_SELECTOR, "span.clip")
                        if clip_spans:
                            clip_text = clip_spans[0].text.strip() or driver.execute_script(
                                "return arguments[0].textContent;", clip_spans[0]).strip()
                            full_text += " " + clip_text if full_text else clip_text

                        if not full_text:
                            ng_spans = button.find_elements(By.CSS_SELECTOR, "span.ng-star-inserted")
                            for span in ng_spans:
                                if "btn_label" not in span.get_attribute("class"):
                                    span_text = span.text.strip() or driver.execute_script(
                                        "return arguments[0].textContent;", span).strip()
                                    full_text += span_text + " "

                        player_name = full_text.strip()
                        if not player_name:
                            player_name = "Brak nazwy"
                    except Exception as e:
                        player_name = f"Brak nazwy (błąd: {e})"

                    odds_value = ""
                    try:
                        odds_elements = button.find_elements(By.CSS_SELECTOR,
                                                             "span.btn_label.ng-star-inserted:not(.is-top)")
                        if not odds_elements:
                            odds_elements = button.find_elements(By.CSS_SELECTOR, "span.btn_label")

                        if odds_elements:
                            for element in odds_elements:
                                if "is-top" in element.get_attribute("class"):
                                    continue
                                text = element.text.strip() or driver.execute_script(
                                    "return arguments[0].textContent;", element).strip()
                                if text == "-" or (text and (text.replace(',', '.').replace('.', '', 1).isdigit() or
                                                             any(c.isdigit() for c in text))):
                                    odds_value = text
                                    break

                            if not odds_value and odds_elements:
                                odds_value = odds_elements[-1].text.strip() or driver.execute_script(
                                    "return arguments[0].textContent;", odds_elements[-1]).strip()

                        if odds_value and odds_value != "-":
                            if not any(c.isdigit() for c in odds_value):
                                for element in button.find_elements(By.CSS_SELECTOR, "span"):
                                    text = element.text.strip() or driver.execute_script(
                                        "return arguments[0].textContent;", element).strip()
                                    if text and (text == "-" or any(c.isdigit() for c in text) and len(text) < 10):
                                        if text not in player_name and len(text) <= 6:
                                            odds_value = text
                                            break

                        if not odds_value:
                            odds_value = "Brak kursu"
                    except Exception as e:
                        odds_value = f"Brak kursu (błąd: {e})"

                    odds_list.append(f"{player_name}: {odds_value}")
                    print(f"Kurs {player_name}: {odds_value}")

                    # Przypisanie kursów do odpowiednich zmiennych
                    if idx == 0:
                        left_odds = odds_value
                    elif idx == 1 and len(odds_buttons) == 3:
                        middle_odds = odds_value
                    elif (idx == 1 and len(odds_buttons) == 2) or (idx == 2 and len(odds_buttons) == 3):
                        right_odds = odds_value

            except Exception as e:
                print(f"Nie udało się pobrać kursów: {e}")

            print("-" * 60)

            # --- Zapis do bazy danych ---
            match_data = {
                'current_global_time': current_polish_time,
                'match_name': match_name,
                'sport_type': sport_name,
                'left_player': left_team,
                'right_player': right_team,
                'match_time': match_time,
                'left_player_score': left_score,
                'right_player_score': right_score,
                'sets_top_player': ", ".join(top_set_scores) if top_set_scores else "",
                'set_current_score_top_player': top_set_current_score,
                'set_subscore_top_player': top_subscore,
                'sets_bottom_player': ", ".join(bottom_set_scores) if bottom_set_scores else "",
                'set_current_score_bottom_player': bottom_set_current_score,
                'set_subscore_bottom_player': bottom_subscore,
                'left_odds': left_odds,
                'middle_odds': middle_odds,
                'right_odds': right_odds
            }
            save_to_database(match_data)

        if not is_active:
            try:
                header = bucket.find_element(By.CSS_SELECTOR, "div.accordionList_header")
                driver.execute_script("arguments[0].click();", header)
            except Exception:
                pass

    # Obliczanie czasu wykonania akcji
    elapsed_time = time.time() - start_time
    print(f"Czas wykonania akcji: {elapsed_time:.2f} sekund")

    # Jeśli minęło mniej niż 60 sekund, czekamy do pełnych 60 sekund
    if elapsed_time < 60:
        wait_time = 60 - elapsed_time
        print(f"Czekam jeszcze {wait_time:.2f} sekund, aby osiągnąć minimum 60 sekund...")
        time.sleep(wait_time)

    # Odblokowanie aktualizacji strony przed odświeżeniem
    unblock_page_updates()

# Główna pętla
try:
    while True:
        process_page()
        print("Odświeżam stronę...")
        driver.refresh()
except KeyboardInterrupt:
    print("\nPrzerwano działanie skryptu przez użytkownika.")
finally:
    driver.quit()