---
tags: [vyzkum, f27, zpravy, intraday]
datum: 2026-11-08
---
# F27 Pokračování po zprávách (NFP, CPI)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f27_f31.py`.

**Kalendář:** `research_data/kalendar_2010_2021.json` (bls.gov archiv), od 2021-09 kalendář z `f7_lib`. Viz [[Zprávy a kalendář]].

## Plán (zapsán PŘED výpočtem)
**Pravidlo** (dny NFP a CPI, zpráva v 8:30 NY):
- **Pohyb** = zavření svíčky 8:44 − otevření svíčky 8:30 (prvních 15 minut).
- **ATR15** = průměrný true range svíček M15 za předchozích 20 obchodních dní.
- **Obchod jen při |pohyb| > 0,5 × ATR15.**
- **Vstup** ve směru pohybu na otevření svíčky 8:45 NY (14:45 Praha).
- **SL** za extrémem prvních 15 minut, **TP** 2R. **Výstup** v 19:45 Praha, když nedojde na SL ani TP.
- **Náklady:** spread brokera podle hodiny a tick na vstupu i výstupu.

**Data:**
- **Vývoj:** HistData SPX+NAS 2010-11 až 2019-02.
- **Kontrola:** broker SPX+NAS 2019-02 až 2026-10.
- **Druhý zdroj:** HistData 2019–2025.
- **Jiné trhy:** broker XAUUSD a EURUSD 2019–2026.

**Náhoda:** jiný den bez zpráv, stejný čas, směr, SL a TP v násobcích ATR15.

**Pravidla rozhodnutí:** stejných 5 bodů jako u [[F22 Průraz úvodního rozpětí (ORB)|F22]], ANO jen když platí vše.

## Výsledky (2026-11-08)
Souhrn: `research_data/f27/f27_souhrn.txt`.

| Část | n | R | t | náhoda |
|---|---|---|---|---|
| Vývoj HistData 2010–19 | 287 | **−0,029** | −0,37 | −0,052 |
| Kontrola broker 2019–26 | 268 | **−0,140** | −2,06 | +0,004 |
| Druhý zdroj HistData 2019–25 | 259 | −0,072 | −1,00 | +0,004 |
| XAUUSD | 126 | −0,125 | −1,29 | −0,037 |
| EURUSD | 113 | −0,168 | −1,76 | −0,076 |

- Pohyb prvních 15 minut po zprávě **nepokračuje**: 55–60 % obchodů končí na SL. Shorty po špatné zprávě jsou nejhorší (kontrola −0,27 R).
- 2026 zatím −15 R.

**Rozhodnutí:** neprošel žádný bod → **BEZ VÝHODY.**
- **Co si vezmeme:** první reakce na NFP/CPI se často vrací. Pro agenta Kalendář to potvrzuje, že je správné se zprávám vyhnout, ne je obchodovat.
