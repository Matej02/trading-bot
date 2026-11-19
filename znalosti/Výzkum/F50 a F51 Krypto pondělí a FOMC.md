---
tags: [vyzkum, f50, f51, krypto, kalendar]
datum: 2026-11-19
---
# F50 a F51 Krypto: pondělí a drift před FOMC

Zadání uživatele (2026-11-19): „Pokračuj dalšími testy.“ Jen test, bot se nemění.

**Data (nic se nestahuje):** FOMC kalendář jako v [[F31 Drift před FOMC|F31]]. Rozdělení jako u [[F29 Krypto momentum|F29]]: vývoj 2014–2021, kontrola 2022–2026.
- **Oprava plánu PŘED výpočtem (2026-11-19):** Binance data jsou jen od 2019 (ne od 2017). Proto:
  - vývoj = broker BTC H1 2014–2021;
  - kontrola = broker H1 2022–2026;
  - druhý zdroj = Binance 1h 2019–2026;
  - ETH = broker H1 od 2017.

**Společné:**
- **Náklady:** spread brokera (BTC ~24 $, ETH ~2,8 $) a swap long za noc (krypto každou noc).
- R = výsledek / ATR20 denního rozpětí (dny UTC).
- **Srovnání (drift):** stejně dlouhé okno ve všech ostatních dnech. Rozhoduje převis.

## F50 Pondělní efekt BTC (plán PŘED výpočtem)
- **Proč:** Caporale a Plastun (2019) popisují vyšší výnos BTC v pondělí.
- **Obchod:** long BTC pondělí 00:00 → úterý 00:00 UTC.
- **Srovnání:** stejné 24h okno v ostatní dny (út–ne).

## F51 Drift před FOMC na BTC (plán PŘED výpočtem)
- **Proč:** drift před FOMC je doložený u rizikových aktiv ([[F31 Drift před FOMC|F31]] na indexech od 2019). Krypto je rizikové aktivum.
- **Obchod:** long BTC od 14:00 NY v den před oznámením do 13:55 NY v den oznámení (jako F31).
- **Srovnání:** stejné okno v ostatní dny.

**Pravidla rozhodnutí (u každého testu zvlášť), ANO jen když platí vše:**
1. Vývoj (broker 2014–2021): událost > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola (broker 2022–2026): událost > 0 a převis > 0 s t ≥ 1,5.
3. ETH: převis > 0 (celé období).
4. Druhý zdroj Binance BTC 2019–2026: převis > 0.
5. Převis kladný aspoň v 60 % let.

Skript `scratch/f50_f51.py`, výstup `research_data/f50/souhrn.txt`.

## Výsledky (2026-11-19)
Souhrn `research_data/f50/souhrn.txt`. Broker BTC H1 má souvislá data až od 2017, vývoj je tedy fakticky 2017–2021.

| Test | Vývoj 2017–21 | Kontrola 2022–26 | Binance 2019–26 | ETH | Roky | Verdikt |
|---|---|---|---|---|---|---|
| **F50** pondělí | převis +0,084 (t 1,31), n 252 | +0,091 (t 1,43), n 214 | +0,070 (t 1,54) | +0,027 | 7 z 10 | **BEZ VÝHODY** (body 1, 2) |
| **F51** před FOMC | +0,086 (t 0,83), n 39 | +0,094 (t 0,87), n 31 | +0,169 (t 1,91) | +0,109 | 5 z 10 | **BEZ VÝHODY** (body 1, 2, 5) |

- **Oba efekty mají správný směr ve všech zdrojích,** ale nejsou statisticky průkazné. U F51 je málo událostí (8× ročně).
- **F50 pondělí:** převis +0,07 až +0,09 R konzistentně ve všech obdobích, ale t pod hranicí. Do simulátoru ne, podle pravidel neprošel.
- Do bota nic.
