---
tags: [vyzkum, f43, proraz, prověrka]
datum: 2026-11-19
---
# F43 Průraz F2 přísná prověrka

Zadání uživatele (2026-11-19): „Ano, pokračuj kontrolou odolnosti a F43. Pokračujme dál a pak dej info, co se nám může hodit celkově od všech, které tam aktuálně nemáme přidané.“

**Proč:**
- [[Průraz F2 (proraz_d1)|Průraz F2]] běží v simulátoru jako `validated`, ale ověřený byl jen na holdoutu 2024–26 (+0,34 R).
- 2009–23 vycházel ~0 R ([[F4 Vstup na menším timeframu|F4]]) a mimo vybrané trhy −0,11 R ([[F3 Průraz na nových trzích|F3]]).
- Teď stejná přísná prověrka jako [[F42 RSI(2) přísná prověrka|F42]]. Jen test, bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Pravidlo jako v simulátoru** (`strategies.ts`):
  - signál na zavření dne: zavření nad maximem předchozích 20 dní a týdenní trend nahoru → long; zavření pod minimem 20 dní a trend dolů → short;
  - **týdenní trend:** týdenní zavření nad EMA50 týdnů a EMA50 roste proti stavu před 3 týdny (dolů opačně);
  - SL 2 ATR14 a TP 4 ATR14 (1:2) od zavření signálního dne;
  - **vstup na otevření dalšího dne;**
  - výstup na SL/TP (oba v jednom dni = SL), jinak na zavření po 48 obchodních dnech;
  - nový vstup na stejném trhu až po výstupu.
- **Srovnání (drift):** stejné vstupy a výstupy ve **všech** dnech s daným týdenním trendem, bez podmínky průrazu. Rozhoduje převis signál − srovnání.
- **Náklady:** půl spreadu brokera na vstupu i výstupu a swap podle směru (krypto každou noc, jinak středa → čtvrtek 3×). R = výsledek / 2 ATR.
- **Hodnotí se po dnech vstupu** (průměr trhů).
- **Data:**
  - trhy F2: BTC, ETH, XAU, EURUSD, GBPUSD, USDJPY, SPX, NAS, DAX;
  - vývoj Yahoo do 2018 (od 1990, krypto od začátku dat);
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026;
  - jiné trhy (nevybrané): US30, FTSE, CAC, XAG, WTI (Yahoo, celé období).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Jiné trhy dohromady: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let.

Skript `scratch/f43_proraz.py`, výstup `research_data/f43/souhrn.txt`.
