---
tags: [vyzkum, f53, f54, rsi2, kovy, forex]
datum: 2026-11-19
---
# F53 a F54 RSI(2) na kovech a měnách (obousměrně)

Zadání uživatele (2026-11-19): „Pokračuj dalšími testy.“

**Proč:**
- Kombinace F33 + RSI(2) ([[F52 Kombinace F33 a RSI(2) pro prop účet|F52]]) funguje, ale je pomalá a celá stojí na US indexech.
- Nejvíc by pomohla výhoda na jiném trhu.
- Princip RSI(2) (krátký přestřel proti dlouhodobému trendu se vrací) se zkusí na kovech a hlavních měnách, **obousměrně**.
- Jen test, bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Long:**
  - zavření > SMA200 a RSI(2) < 10 → vstup na otevření dalšího dne;
  - výstup zavření > SMA5, stop 3 ATR20, nejdéle 10 dní.
- **Short (zrcadlově):**
  - zavření < SMA200 a RSI(2) > 90;
  - výstup zavření < SMA5, stop 3 ATR nad vstupem.
- Na jednom trhu nejvýš jedna pozice.
- **Srovnání (drift):** stejné vstupy a výstupy ve všech dnech ve směru SMA200 (long nad, short pod). Rozhoduje převis.
- **Náklady:** půl spreadu na vstupu i výstupu, swap podle směru (středa 3×). R = výsledek / 3 ATR.
- **Hodnotí se po dnech vstupu** (průměr trhů).

**F53 Kovy:**
- XAU, XAG;
- vývoj Yahoo 2000–2018, kontrola Yahoo 2019–2026, druhý zdroj broker 2019–2026;
- jiný trh XPT.

**F54 Měny:**
- EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD;
- vývoj Yahoo do 2018, kontrola Yahoo 2019–2026, druhý zdroj broker 2019–2026;
- jiné trhy: křížové páry EURJPY, GBPJPY, AUDJPY, EURCAD, GBPNZD (dohromady).

**Pravidla rozhodnutí (u každého testu zvlášť), ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Jiné trhy: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let.

Skript `scratch/f53_f54.py`, výstup `research_data/f53/souhrn.txt`.
