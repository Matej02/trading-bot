---
tags: [vyzkum, f44, vix, strach]
datum: 2026-11-19
---
# F44 Struktura VIX (panika → odraz indexů)

Zadání uživatele (2026-11-19): „Ano, stáhni data a pokračuj.“

**Data:** Yahoo ^VIX (od 1990) a ^VIX3M (od 2006-07), staženo se souhlasem uživatele do `research_data/f44`.

**Proč:**
- Když je 30denní očekávaná volatilita (VIX) vyšší než 3měsíční (VIX3M), trh je v panice (backwardation).
- Podle literatury (např. Simon a Campasano, Johnson 2017) po takových dnech indexy v průměru rostou víc než jindy.
- Jiný druh signálu než F33 (kalendář) a RSI(2) (cena). Jen test, bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Signál** na zavření dne: VIX / VIX3M ≥ 1,0.
- **Vstup** long na otevření dalšího dne, **výstup** na zavření 5. obchodního dne. Pojistný stop 3 ATR20 (přes low, při gapu za otevírací cenu). Nový vstup až po výstupu.
- **Trhy:** SPX, NAS (hlavní), jiné trhy US30, DAX, FTSE.
- **Náklady:** půl spreadu na vstupu i výstupu, swap long za noc. R = výsledek / 3 ATR.
- **Srovnání (drift):** stejné vstupy a výstupy ve všech dnech. Rozhoduje převis.
- **Hodnotí se po dnech vstupu** (průměr SPX a NAS).
- **Data:**
  - vývoj Yahoo 2006-07 až 2018;
  - kontrola Yahoo 2019–2026;
  - druhý zdroj broker H1 → denní 2019–2026.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. US30, DAX i FTSE: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let se signálem.

Skript `scratch/f44_vix.py`, výstup `research_data/f44/souhrn.txt`.
