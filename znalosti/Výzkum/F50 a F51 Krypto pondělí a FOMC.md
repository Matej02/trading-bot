---
tags: [vyzkum, f50, f51, krypto, kalendar]
datum: 2026-11-19
---
# F50 a F51 Krypto: pondělí a drift před FOMC

Zadání uživatele (2026-11-19): „Pokračuj dalšími testy.“ Jen test, bot se nemění.

**Data (nic se nestahuje):** Binance BTCUSDT a ETHUSDT 1h od 2017, broker BTC/ETH H1 2019–2026. FOMC kalendář jako v [[F31 Drift před FOMC|F31]]. Rozdělení jako u [[F29 Krypto momentum|F29]]: vývoj 2017–2021, kontrola 2022–2026.

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
1. Vývoj Binance 2017–2021: událost > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola Binance 2022–2026: událost > 0 a převis > 0 s t ≥ 1,5.
3. ETH: převis > 0 (celé období).
4. Broker BTC 2019–2026: převis > 0.
5. Převis kladný aspoň v 60 % let.

Skript `scratch/f50_f51.py`, výstup `research_data/f50/souhrn.txt`.
