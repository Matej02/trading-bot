---
tags: [vyzkum, f58, f59, forex, indexy, denni-doba]
datum: 2026-11-20
---
# F58 a F59 Měny v místních hodinách a Turnaround Tuesday

Zadání uživatele (2026-11-20): „Na nic nesahej, ale testuj dál, dokud nezjistíš něco, co se nám zase bude hodit nebo bude dobré na testování.“ Jen test, bot ani simulátor se nemění.

**Proč:**
- **F58:** měna v průměru slábne během obchodních hodin své země a sílí v hodinách ostatních (Breedon a Ranaldo 2013, „Intraday patterns in FX returns and order flow“). Jiný typ jevu než dosavadní testy na měnách (F35 fixing, F48 gotobi, F54 RSI(2)).
- **F59:** Turnaround Tuesday, odraz US indexů v úterý po poklesu v pondělí. Rodina krátkého návratu, která na US indexech funguje ([[F42 RSI(2) přísná prověrka|F42]]).

## Plán (zapsán PŘED výpočtem)
**F58 Měny v místních hodinách** (čas Londýn, Po–Pá):
- **Okno místních hodin, cizí měna slábne:**
  - EUR, GBP, CHF 07:00 → 12:00: short EURUSD a GBPUSD, long USDCHF;
  - JPY, AUD, NZD 00:00 → 06:00: long USDJPY, short AUDUSD a NZDUSD.
- **Okno amerických hodin po zavření Londýna, USD slábne:** 16:00 → 21:00: long EURUSD, GBPUSD, AUDUSD, NZDUSD; short USDJPY a USDCHF.
- Vstup na otevření první svíčky v čase začátku, výstup na zavření poslední svíčky před koncem. Bez SL a TP.
- **Náklady:** půl spreadu brokera podle hodiny na vstupu i výstupu, swap za noc, pokud okno přechází půlnoc UTC (středa 3×).
- R = výsledek / ATR20 (denní, Londýn).
- **Srovnání:** stejný pár, stejný směr a stejná délka okna se začátkem v ostatních celých hodinách dne.
- Hodnotí se po dnech (průměr všech obchodů dne).
- **Data:**
  - hlavní trhy EURUSD, GBPUSD, USDJPY z HistData M1 (vývoj 2010–2018, kontrola 2019–2025);
  - druhý zdroj H1 brokera 2019–2026;
  - jiné trhy AUDUSD, NZDUSD, USDCHF z H1 brokera 2010–2026.

**F59 Turnaround Tuesday:**
- Když pondělní zavření < páteční zavření → long od pondělního zavření do úterního zavření.
- R = výsledek / ATR20, náklady půl spreadu + swap za noc.
- **Srovnání:** zavření → zavření ve všech ostatních dnech.
- Trhy US: SPX500, NAS100, US30. Jiné trhy: DAX, FTSE, CAC.
- Vývoj Yahoo 1990–2018, kontrola Yahoo 2019–2026, broker 2019–2026.
- Popis (nerozhoduje): totéž s vstupem na úterní otevření (realističtější, PC večer neběží).

**Pravidla rozhodnutí (u každého testu zvlášť), ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Jiné trhy: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let.

Skript `scratch/f58_f59.py`, výstup `research_data/f58/souhrn.txt`.

## Výsledky (2026-11-20)
Souhrn `research_data/f58/souhrn.txt`.

| Test | Vývoj | Kontrola | Broker 2019+ | Jiné trhy | Roky | Verdikt |
|---|---|---|---|---|---|---|
| **F58** měny v místních hodinách | −0,034 R, převis −0,004 (t −1,09) | −0,046, převis −0,012 (t −2,59) | −0,039, převis −0,007 | −0,022 | 19 % | **BEZ VÝHODY** |
| **F59** Turnaround Tuesday | +0,060, převis +0,045 (t 1,53) | +0,022, převis −0,009 (t −0,17) | +0,112, převis +0,087 | +0,026 | 54 % | **BEZ VÝHODY** |

- **F58:** po nákladech všechno ztrátové (spread ~0,03 R na obchod, pohyb za 5 h je malý).
  - Popis po oknech: evropské dopoledne (short EUR a GBP, long USDCHF) má převis t ~3, americké odpoledne je naopak záporné. Zjištěno **po výpočtu** a i tak po nákladech nula, takže se dál nehodnotí.
- **F59:** do 2018 slabý náznak, od 2019 nic.
