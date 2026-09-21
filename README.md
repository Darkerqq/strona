# Planer zadan

Aplikacja webowa Flask do planowania zadan, sledzenia postepow, prowadzenia notatek i organizowania pracy wedlug dni. Dane sa przechowywane lokalnie w bazie SQLite, a kazdy uzytkownik ma osobne zadania, historie i notatki.

## Spis tresci

1. [Najwazniejsze funkcje](#najwazniejsze-funkcje)
2. [Wymagania](#wymagania)
3. [Uruchomienie](#uruchomienie)
4. [Logowanie i konta](#logowanie-i-konta)
5. [Dashboard](#dashboard)
6. [Zadania](#zadania)
7. [Kalendarz](#kalendarz)
8. [Notatki](#notatki)
9. [Historia i statystyki](#historia-i-statystyki)
10. [Przypomnienia](#przypomnienia)
11. [Baza danych](#baza-danych)
12. [Bezpieczenstwo](#bezpieczenstwo)
13. [Struktura projektu](#struktura-projektu)
14. [Trasy HTTP](#trasy-http)
15. [Konfiguracja produkcyjna](#konfiguracja-produkcyjna)
16. [Rozwiazywanie problemow](#rozwiazywanie-problemow)

## Najwazniejsze funkcje

- rejestracja i logowanie uzytkownikow,
- bezpieczne hashowanie hasel,
- osobne dane dla kazdego uzytkownika,
- dashboard z wykresem realizacji zadan,
- nawigacja wykresu po dniach oraz powrot do dzisiaj,
- zadania codzienne, jednorazowe i czasowe,
- priorytety, kategorie, kolory i terminy,
- oznaczanie zadan jako wykonane, niewykonane lub nieuzupelnione,
- serie kolejnych wykonanych dni,
- wstrzymywanie i wznawianie zadan,
- podglad zadan na najblizsze 7 dni,
- miesieczny kalendarz z podgladem zadan,
- dodawanie, edycja, usuwanie i przypinanie notatek,
- historia realizacji,
- API przypomnien.

## Wymagania

- Python 3.10 lub nowszy,
- Flask,
- Werkzeug,
- SQLite,
- PowerShell na Windows albo odpowiednik terminala na innym systemie.

Projekt zawiera lokalne srodowisko `venv`, ale nie powinno ono byc dodawane do repozytorium. Jest ignorowane przez `.gitignore`.

## Uruchomienie

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

Nastepnie otworz:

```text
http://127.0.0.1:5000
```

Jesli srodowisko `venv` nie istnieje:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install flask werkzeug
python app.py
```

Przy pierwszym uruchomieniu aplikacja tworzy katalog `data/` oraz baze `data/tasks.db`.

## Logowanie i konta

Aplikacja wymaga zalogowania przed dostepem do dashboardu i pozostalych podstron.

### Rejestracja

Adres: `/register`

Podczas rejestracji:

- login musi miec od 3 do 40 znakow,
- haslo musi miec co najmniej 8 znakow,
- haslo trzeba wpisac dwukrotnie,
- login musi byc unikalny.

Po poprawnej rejestracji uzytkownik zostaje zalogowany automatycznie.

### Logowanie

Adres: `/login`

Uzytkownik podaje login i haslo. Po poprawnym logowaniu otrzymuje sesje Flask i moze korzystac ze swoich danych.

### Wylogowanie

Wylogowanie odbywa sie przez formularz `POST` na `/logout`. Sesja zostaje wyczyszczona.

## Dashboard

Adres: `/`

Dashboard jest strona glowna aplikacji. Zawiera:

- statystyki miesiecznej skutecznosci,
- liczbe wszystkich ukonczonych zadan,
- liczbe aktywnych zadan dla wybranego dnia,
- wykres realizacji z ostatnich 7 dni,
- przyciski przejscia do poprzedniego i nastepnego dnia,
- przycisk powrotu do dzisiejszej daty,
- liste najblizszych zadan dla wybranego dnia,
- panel przypomnien,
- skroty do kalendarza i notatek,
- liste przypietych notatek.

Wybrany dzien mozna przekazac parametrem:

```text
/?date=2026-09-24
```

W przypadku zadania codziennego dashboard pokazuje date rozpoczecia oraz informacje, ze zadanie powtarza sie codziennie. Dzieki temu data utworzenia nie jest mylona z aktualnie ogladanym dniem.

## Zadania

Adres: `/tasks`

Widok zadan pozwala zarzadzac zadaniami dla wybranego dnia.

### Typy zadan

#### Codzienne

Zadanie jest widoczne od daty utworzenia w kolejnych dniach, dopoki nie zostanie wstrzymane lub usuniete.

#### Jednorazowe

Zadanie jest przypisane do dnia utworzenia. Moze pozostac widoczne w historii, jesli ma zapisany status.

#### Na X dni

Zadanie jest aktywne przez okres wybranej liczby dni, liczac od daty utworzenia.

### Dane zadania

Podczas dodawania lub edycji mozna ustawic:

- tytul,
- opis,
- typ,
- liczbe dni dla zadania czasowego,
- priorytet: niski, normalny albo wysoki,
- kategorie,
- kolor,
- godzine wykonania,
- termin,
- wlaczenie przypomnienia,
- liczbe minut przed terminem.

### Statusy

Kazde zadanie moze miec jeden z trzech statusow:

- `pending` - nieuzupelnione,
- `completed` - wykonane,
- `failed` - niewykonane.

Zmiana statusu aktualizuje historie dla wybranego dnia.

### Serie

Dla wykonanych zadan aplikacja oblicza liczbe kolejnych dni z rzedu. Seria zatrzymuje sie, gdy brakuje wpisu lub status nie jest rowny `completed`.

### Wstrzymywanie

Zadanie codzienne mozna wstrzymac. Wstrzymane zadanie trafia do sekcji archiwum i mozna je wznowic od wybranego dnia.

### Najblizsze 7 dni

Pod lista zadan znajduje sie tygodniowy podglad. Kazdy dzien pokazuje:

- date,
- dzien tygodnia,
- tytuly zadan,
- liczbe pozostalych zadan, gdy jest ich wiecej niz trzy.

Klikniecie dnia otwiera liste zadan dla tej daty.

## Kalendarz

Adres: `/calendar`

Kalendarz pokazuje caly miesiac wybranej daty. Kazdy dzien moze zawierac:

- tytuly pierwszych zadan,
- kolory zadan,
- informacje o dodatkowych zadaniach,
- oznaczenie dzisiaj,
- oznaczenie wybranego dnia.

Klikniecie dnia przechodzi do `/tasks?date=YYYY-MM-DD`.

Przyciski strzalek zmieniaja miesiac, a przycisk `Dzisiaj` wraca do aktualnej daty.

## Notatki

Adres: `/notes`

Notatki sa przypisane do daty i uzytkownika.

Dostepne operacje:

- dodanie tytulu i tresci,
- edycja notatki,
- przypiecie notatki,
- odpiecie notatki,
- usuniecie notatki,
- przechodzenie do notatek z poprzedniego i nastepnego dnia.

### Przypiete notatki

Przypieta notatka pojawia sie w panelu `Przypiete notatki` na dashboardzie. Widoczna jest niezaleznie od aktualnie wybranej daty, co pozwala trzymac wazne informacje stale pod reka.

## Historia i statystyki

Adres: `/history`

Historia zawiera wpisy statusow zadan pogrupowane wedlug daty. Kazdy wpis pokazuje:

- date,
- nazwe zadania,
- status wykonania.

Dashboard dodatkowo liczy:

- wykonane zadania w wybranym miesiacu,
- niewykonane zadania w wybranym miesiacu,
- laczna liczbe wpisow miesiecznych,
- procent skutecznosci,
- wszystkie wykonane zadania uzytkownika.

Wzor skutecznosci jest liczony jako:

```text
((wykonane - niewykonane) / wszystkie wpisy) * 100
```

## Przypomnienia

Przypomnienia sa konfigurowane na poziomie zadania przez:

- godzine `due_time`,
- wlacznik `reminder_enabled`,
- liczbe minut `reminder_minutes`.

### API

```text
GET /api/reminders?date=2026-09-21
```

API zwraca przypomnienia zalogowanego uzytkownika dla zadan utworzonych nie pozniej niz podana data.

Przykladowa odpowiedz:

```json
[
  {
    "id": 12,
    "title": "Spotkanie",
    "due_time": "09:30",
    "reminder_minutes": 15,
    "color": "#3b82f6",
    "priority": "high"
  }
]
```

## Baza danych

Baza znajduje sie w:

```text
data/tasks.db
```

### Tabele

#### `users`

Przechowuje konta uzytkownikow:

- `id`,
- `username`,
- `password_hash`,
- `created_at`.

#### `tasks`

Przechowuje zadania i ich ustawienia:

- tresc i opis,
- date utworzenia,
- typ i czas trwania,
- priorytet, kategorie i kolor,
- godzine oraz termin,
- ustawienia przypomnien,
- `user_id`.

#### `task_history`

Przechowuje status zadania dla konkretnej daty. Para `task_id` i `date` jest unikalna.

#### `pause_periods`

Przechowuje okresy wstrzymania zadan.

#### `notes`

Przechowuje notatki:

- tytul,
- tresc,
- date,
- daty utworzenia i aktualizacji,
- `is_pinned`,
- `user_id`.

### Migracje

Funkcja `init_db()` tworzy brakujace tabele i dodaje brakujace kolumny przez `ALTER TABLE`. Migracje nie usuwaja istniejacych danych.

## Bezpieczenstwo

- Hasla sa przechowywane jako hashe tworzone przez `generate_password_hash`.
- Hasel nie da sie odczytac z bazy w oryginalnej postaci.
- Logowanie sprawdza haslo przez `check_password_hash`.
- Kazdy chroniony endpoint wymaga aktywnej sesji.
- Zapytania do zadan i notatek filtruja `user_id`.
- Operacje edycji, usuwania, przypinania i zmiany statusu sprawdzaja wlasciciela rekordu.
- Parametr przekierowania po logowaniu jest ograniczony do sciezek lokalnych.
- Zapytania do SQLite uzywaja parametrow zamiast laczenia danych z SQL.

## Struktura projektu

```text
strona/
|-- app.py
|-- README.md
|-- .gitignore
|-- data/
|   `-- tasks.db                 # lokalna baza, ignorowana przez Git
|-- static/
|   |-- css/
|   |   `-- style.css
|   `-- js/
|       `-- app.js
|-- templates/
|   |-- base.html
|   |-- dashboard.html
|   |-- tasks.html
|   |-- calendar.html
|   |-- notes.html
|   |-- history.html
|   |-- login.html
|   |-- register.html
|   `-- index.html                # starszy, nieuzywany szablon
`-- venv/                         # lokalne srodowisko, ignorowane przez Git
```

## Trasy HTTP

### Widoki publiczne

| Metoda | Adres | Opis |
|---|---|---|
| `GET`, `POST` | `/login` | Logowanie |
| `GET`, `POST` | `/register` | Rejestracja |
| `POST` | `/logout` | Wylogowanie |

### Widoki wymagajace logowania

| Metoda | Adres | Opis |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/tasks` | Zadania |
| `GET` | `/calendar` | Kalendarz |
| `GET` | `/notes` | Notatki |
| `GET` | `/history` | Historia |

### Operacje na zadaniach

| Metoda | Adres | Opis |
|---|---|---|
| `POST` | `/add` | Dodawanie zadania |
| `POST` | `/edit_task/<task_id>` | Edycja zadania |
| `POST` | `/update_status` | Zmiana statusu |
| `POST` | `/pause_task/<task_id>` | Wstrzymanie zadania |
| `POST` | `/resume_task/<task_id>` | Wznowienie zadania |
| `POST` | `/delete/<task_id>` | Usuniecie zadania |

### Operacje na notatkach

| Metoda | Adres | Opis |
|---|---|---|
| `POST` | `/add_note` | Dodawanie notatki |
| `POST` | `/edit_note/<note_id>` | Edycja notatki |
| `POST` | `/toggle_note_pin/<note_id>` | Przypiecie lub odpiecie |
| `POST` | `/delete_note/<note_id>` | Usuniecie notatki |

### API

| Metoda | Adres | Opis |
|---|---|---|
| `GET` | `/api/reminders?date=YYYY-MM-DD` | Przypomnienia zalogowanego uzytkownika |

## Konfiguracja produkcyjna

Ustaw wlasny sekret sesji zamiast polegac na losowej wartosci generowanej przy starcie:

### PowerShell

```powershell
$env:FLASK_SECRET_KEY = "dlugi-losowy-sekret"
python app.py
```

W produkcji zalecane jest dodatkowo:

- uzycie serwera WSGI zamiast trybu developerskiego,
- wylaczenie `debug=True`,
- przechowywanie sekretu poza kodem,
- regularne kopie zapasowe `data/tasks.db`,
- uruchomienie aplikacji za HTTPS.

## Rozwiazywanie problemow

### Blad brakujacej kolumny SQLite

Uruchom aplikacje ponownie. `init_db()` wykona migracje brakujacych kolumn. Nie usuwaj `tasks.db`, jesli chcesz zachowac dane.

### Przekierowanie do logowania

Sprawdz, czy sesja nie wygasla. Zaloguj sie ponownie na `/login`.

### Brak przypomnien

Sprawdz, czy zadanie ma:

- ustawiona godzine,
- zaznaczone przypomnienie,
- poprawna date utworzenia.

### Git dodaje baze lub venv

Sprawdz `.gitignore`. Jesli plik byl juz wczesniej dodany do indeksu Git, usun go z indeksu bez kasowania z dysku:

```powershell
git rm --cached data/tasks.db
git rm -r --cached venv
```

Nastepnie dodaj pliki ponownie:

```powershell
git add .
git status
```
