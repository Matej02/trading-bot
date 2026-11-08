---
tags: [vyzkum, f32, momentum, rotace, mesicni]
datum: 2026-11-08
---
# F32 Rotace podle relativní síly

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f32_rotace.py`.

## Plán (zapsán PŘED výpočtem)
**Vesmír A (15 trhů):** SPX500, NAS100, US30, DAX, FTSE, CAC, XAU, XAG, CRUDE_OIL, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD.

**Pravidlo:**
- **Skóre:** první obchodní den měsíce se spočte 126denní výnos / 126denní směrodatná odchylka denních výnosů. Jen data do předchozího dne.
- **Pozice:** long 3 trhy s nejvyšším skóre, stejné váhy, drží se měsíc.
- **Náklady:** půl spreadu brokera na vstupu i výstupu, jen když se pozice mění; swap za každou noc.
- **Popisně:** varianta long 3 nejlepší / short 3 nejhorší.

**Srovnání:** stejně vážený long všech 15 trhů se stejnými náklady.

**Data:**
- **Vývoj:** Yahoo 2007–2018.
- **Kontrola:** Yahoo 2019–2026.
- **Druhý zdroj:** H1 brokera → denní, 2019–2026.
- **Jiné trhy:** vesmír B = ostatní trhy z F6 (forex křížové páry, evropské indexy, Brent, platina).

**Pravidla rozhodnutí (měsíční výnosy portfolia), ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. Vesmír B v kontrole > 0.
4. Sharpe vyšší než srovnání ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-08)
Souhrn: `research_data/f32/f32_souhrn.txt`.

| Část | Rotace %/měs | t | Sharpe | Všechny long Sharpe | Max propad |
|---|---|---|---|---|---|
| Vývoj Yahoo 2007–2018 | +0,35 | 0,98 | 0,28 | 0,19 | 30 % |
| Kontrola Yahoo 2019+ | +0,68 | 1,59 | **0,57** | **0,76** | 22 % |
| Vesmír B 2019+ | +0,48 | 0,96 | 0,35 | 0,85 | 16 % |
| Druhý zdroj broker 2019+ | +1,07 | 2,18 | 0,80 | 0,70 | – |

- V top 3 jsou nejčastěji US indexy a zlato. Rotace je hlavně „drž, co roste“, tedy zase hlavně long indexy.
- Ve vesmíru B dominují páry s tureckou lirou (USDTRY, GBPTRY, EURTRY).
- **Zdroj dat mění závěr:** na Yahoo je rotace horší než držet vše, na datech brokera lepší.
- Long/short varianta: vývoj +0,09 %/měs, kontrola −0,19 %/měs.

**Rozhodnutí:** 1 NE (t 0,98), 2 ANO, 3 ANO, 4 NE (v kontrole horší Sharpe než držet vše), 5 ANO → **BEZ VÝHODY.**
