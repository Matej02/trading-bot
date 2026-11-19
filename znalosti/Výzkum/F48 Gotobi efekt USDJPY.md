---
tags: [vyzkum, f48, gotobi, usdjpy, kalendar]
datum: 2026-11-19
---
# F48 Gotobi efekt (USDJPY)

Zadání uživatele (2026-11-19): „Dobře, pokračuj dalšími testy.“

**Proč:**
- Japonští dovozci platí faktury v „gotobi“ dny (5., 10., 15., 20., 25., 30. a poslední pracovní den měsíce). Dolary nakupují před tokijským fixingem v 9:55 JST.
- USDJPY proto ráno v tyto dny roste (Bessho, Hattori a kol. 2023; tržní praxe).
- Tok peněz z kalendáře jako F33, ale na jiném trhu a nezávislý. Jen test, bot se nemění.

## Plán (zapsán PŘED výpočtem)
- **Den gotobi:**
  - pracovní den, který je 5., 10., 15., 20., 25. nebo 30. v měsíci, nebo poslední pracovní den měsíce;
  - když takové datum padne na víkend, platí předchozí pátek;
  - japonské svátky se nezohledňují (zjednodušení).
- **Obchod:** long USDJPY od 08:00 JST do 09:55 JST (fixing), tj. 23:00 UTC předchozího dne → 00:55 UTC. Japonsko nemá letní čas.
  - Na H1 brokera: otevření svíčky 23:00 UTC → otevření svíčky 01:00 UTC.
- **Náklady:** spread brokera podle hodiny. Swap se neplatí (okno je mimo rollover 21–22 UTC). R = výsledek / ATR20 denního rozpětí.
- **Srovnání:** stejné okno ve všech ostatních všedních dnech. Rozhoduje převis.
- **Data:**
  - vývoj HistData M1 2010–2018 (čas NY s letním časem → UTC, ověřeno);
  - kontrola broker H1 2019–2026;
  - druhý zdroj HistData M1 2019–2025;
  - jiný trh EURJPY (broker H1 2019–2026).

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: gotobi > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: gotobi > 0 a převis > 0 s t ≥ 1,5.
3. Druhý zdroj 2019–2025: převis > 0.
4. EURJPY: převis > 0.
5. Převis kladný aspoň v 60 % let.

Skript `scratch/f48_gotobi.py`, výstup `research_data/f48/souhrn.txt`.
