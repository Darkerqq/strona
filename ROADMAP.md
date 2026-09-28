# Koncepcja rozwoju Planera

Planer ma być prostym, osobistym narzędziem do organizowania codziennych obowiązków, planowania pracy i śledzenia postępów.

## Główne obszary

- **Zadania i planowanie** – tworzenie zadań jednorazowych, cyklicznych i ograniczonych czasowo, z priorytetami, terminami oraz możliwością śledzenia postępów.
- **Przegląd pracy** – dashboard, kalendarz i historia pomagające planować dni, obserwować realizację zadań i wracać do wcześniejszych aktywności.
- **Notatki i przypomnienia** – zapisywanie informacji powiązanych z dniem oraz szybki dostęp do ważnych notatek i terminów.
- **Konta i prywatność** – osobista przestrzeń użytkownika, w której zadania i notatki są oddzielone od danych innych osób.

## Założenia

- Czytelny interfejs, który ułatwia szybkie planowanie i codzienne korzystanie.
- Bezpieczne logowanie, hashowanie haseł i kontrola dostępu do danych użytkownika.
- Prosta, trwała baza danych oraz możliwość dalszego rozwoju aplikacji.

## Kierunek

Rozwijać Planer jako lekką aplikację webową łączącą planowanie zadań, organizację informacji i podsumowanie postępów w jednym miejscu.




Dokładny plan

# Roadmapa projektu Planer

Dokument porządkuje kroki rozwoju aplikacji od podstawowej konfiguracji do zestawu funkcji opisanego w kodzie, szablonach i dokumentacji. Kolejność przedstawia logiczną ścieżkę budowy produktu, a nie daty ani historię commitów.

## 1. Uruchomienie projektu

- Przygotowanie aplikacji w Pythonie z Flaskiem.
- Uporządkowanie plików na backend, szablony HTML, arkusz stylów, JavaScript i dane lokalne.
- Dodanie instrukcji instalacji zależności, utworzenia środowiska wirtualnego i uruchamiania serwera.

## 2. Trwałe przechowywanie danych

- Wykorzystanie SQLite do przechowywania danych między uruchomieniami aplikacji.
- Utworzenie tabel dla zadań, dziennej historii statusów i okresów wstrzymania.
- Dodanie inicjalizacji bazy oraz mechanizmu uzupełniania brakujących kolumn bez usuwania istniejących danych.

## 3. Podstawowa obsługa zadań

- Dodawanie zadań z tytułem, opisem i datą rozpoczęcia.
- Wyświetlanie zadań dla wybranego dnia.
- Edytowanie i usuwanie zadań.
- Zmianę dziennego statusu na wykonane lub niewykonane oraz usuwanie wpisu, aby przywrócić stan oczekujący.

## 4. Typy i cykl życia zadań

- Wprowadzenie zadań codziennych, jednorazowych i ograniczonych do określonej liczby dni.
- Uwzględnianie typu zadania i zapisanej historii przy ustalaniu, w które dni zadanie ma być widoczne.
- Dodanie wstrzymywania i wznawiania zadań oraz obliczania serii kolejnych wykonań.

## 5. Priorytety i szczegóły planowania

- Rozszerzenie zadań o priorytet, kategorię i kolor.
- Dodanie planowanej godziny, terminu oraz ustawień przypomnienia.
- Wykorzystanie priorytetów do porządkowania list zadań.

## 6. Konta użytkowników i prywatność danych

- Dodanie rejestracji, logowania, sesji użytkownika i wylogowania.
- Zabezpieczenie haseł przez ich hashowanie.
- Powiązanie zadań i notatek z właścicielem oraz ograniczenie widoków i operacji do danych zalogowanej osoby.
- Zachowanie wcześniej zapisanych, nieprzypisanych danych podczas pierwszej rejestracji.

## 7. Dashboard i dzienny przegląd

- Przygotowanie strony głównej z podsumowaniem dnia i miesiąca.
- Dodanie statystyk wykonanych zadań oraz wykresu skuteczności z siedmiu dni.
- Umożliwienie przechodzenia do poprzedniej i następnej daty oraz szybkiego powrotu do dzisiaj.
- Pokazanie zadań na wybrany dzień, skrótów do pozostałych sekcji i przypiętych notatek.

## 8. Widok zadań i planowanie w czasie

- Przygotowanie osobnej strony do dodawania, edycji, zmiany statusów i zarządzania zadaniami.
- Dodanie podglądu zadań na kolejnych siedem dni.
- Wydzielenie zadań wstrzymanych i umożliwienie ich wznowienia.
- Dodanie miesięcznego kalendarza z oznaczeniami zadań i nawigacją między miesiącami.

## 9. Notatki przypisane do dat

- Dodanie notatek z tytułem, treścią i datą.
- Udostępnienie usuwania i przypinania notatek; endpoint edycji jest zaimplementowany, ale formularz edycji nie otwiera się obecnie z poziomu interfejsu.
- Pokazywanie przypiętych notatek na dashboardzie i przechodzenie do dnia, którego dotyczą.

## 10. Historia i statystyki realizacji

- Grupowanie zapisanych statusów według daty i prezentowanie ich na stronie historii.
- Obliczanie miesięcznej skuteczności, liczby wykonanych zadań i łącznej liczby wpisów.
- Pokazywanie serii kolejnych dni wykonania przy zadaniach.

## 11. Przypomnienia

- Udostępnienie API zwracającego dane przypomnień dla zalogowanego użytkownika i wybranej daty.
- Pobieranie danych po stronie przeglądarki i wyświetlanie ich w panelu dashboardu.
- Powiązanie przypomnienia z godziną zadania i wyprzedzeniem ustawionym przez użytkownika.

## 12. Wspólna nawigacja i interakcje interfejsu

- Zbudowanie wspólnego układu stron z nawigacją między dashboardem, zadaniami, kalendarzem, notatkami i historią.
- Dodanie formularzy logowania i rejestracji oraz komunikatów o błędach.
- Wykorzystanie JavaScriptu do wykresu, interakcji formularzy zadań i asynchronicznego ładowania przypomnień; kalendarz jest renderowany po stronie serwera i obsługiwany przez linki nawigacyjne.

## 13. Instrukcje utrzymania i uruchomienia

- Opisanie struktury projektu, dostępnych tras i tabel bazy danych.
- Dodanie wskazówek dotyczących sekretu sesji, kopii zapasowych, HTTPS i serwera WSGI.
- Uwzględnienie lokalnej bazy i środowiska wirtualnego w zasadach ignorowania plików repozytorium.

## Zakres techniczny

Aplikacja jest lokalnym projektem Flask z bazą SQLite i interfejsem renderowanym przez szablony Jinja. Przypomnienia są obecnie udostępniane jako dane przez API i prezentowane na dashboardzie; projekt nie zawiera osobnego procesu dostarczającego powiadomienia w tle.