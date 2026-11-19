---
tags: [vyzkum, f40, f33, kalendar, mesicni]
datum: 2026-11-19
---
# F40 F33 na dalších indexech (Evropa)

Zadání uživatele (2026-11-19): „Ano, pokračuj s rozšířením F33.“ Plus pravidlo: do bota jen to, u čeho si budeme „na 100 % jistí“. Při pochybnosti na bota nesahat.

Rozšíření [[F33 Rebalancování na konci měsíce|F33]] (prošlo na SPX/NAS, kladné i na US30 a DAX). Jen test, bot se nemění. Skript `scratch/f40_f33_evropa.py`, výstup `research_data/f40/souhrn.txt`.

## Plán (zapsán PŘED výpočtem)
- **Trhy:** FTSE 100 (GBR_100), CAC 40 (FRA_40), EuroStoxx 50 (EUR_50), IBEX 35 (ESP_35). US30 a DAX už byly v testu F33.
- **Pravidlo beze změny proti F33:**
  - signál SPY − TLT od konce předchozího měsíce do L−3, obchod jen při |rozdíl| ≥ 2 p. b.;
  - akcie vedly → short, dluhopisy vedly → long;
  - vstup na otevření L−2, výstup na zavření posledního obchodního dne L. Kalendář podle SPY.
- **Náklady:** půl spreadu brokera na vstupu i výstupu, swap za noci. R = výsledek / ATR20, bez stopu.
- **Hodnotí se po měsících:** průměr 4 trhů v daném měsíci.
- **Data:**
  - vývoj Yahoo 2003–2018 (EuroStoxx od 2007);
  - kontrola Yahoo 2019–2026;
  - druhý zdroj H1 brokera → denní 2019–2026.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. Každý ze 4 trhů zvlášť > 0 (celé období).
4. Lepší než stále long ve stejných dnech, ve vývoji i v kontrole.
5. Druhý zdroj > 0.

**Jen popis (nerozhoduje):**
- korelace měsíčních R Evropa vs. SPX/NAS: stejný signál ve stejných dnech znamená spíš větší pozici než rozložení rizika;
- praktický výstup na zavření evropské seance v 17:30 Praha: s PC zapnutým do 20:00 by šlo bez serveru.

## Výsledky (2026-11-19)
Souhrn `research_data/f40/souhrn.txt`. Signál ve 201 měsících.

| Část | Měsíců | R | t | výhra | stále long |
|---|---|---|---|---|---|
| Vývoj 2003–2018 | 137 | **+0,401** | **4,55** | 62 % | +0,021 |
| Kontrola 2019–2026 | 63 | +0,094 | 0,64 | 52 % | −0,134 |
| Broker 2019–2026 | 55 | +0,074 | 0,52 | 49 % | −0,138 |

- **Po trzích 2003–2026:** FTSE +0,420 R (t 4,63), CAC +0,274, EuroStoxx +0,274, IBEX +0,253. Všechny kladné, prosté držení kolem nuly.
- **Po letech:** kladné 20 z 24 let. Ztrátové 2003, 2019, 2020 a 2023.
- **Popis:**
  - korelace s F33 na SPX/NAS po měsících 0,61, tedy spíš větší pozice než rozložení rizika;
  - kombinace US + Evropa +0,293 R (t 4,18), jen US +0,282 R (t 3,54).

## Rozhodnutí podle pravidel zapsaných předem
- Body 1, 3, 4 a 5 ANO. **Bod 2 NE** (kontrola +0,094 R, t 0,64). **⇒ BEZ VÝHODY**, do bota ne. Odpovídá to pravidlu uživatele „jen když jsme si 100% jistí“.
- **Důležité pro F33 samotnou:**
  - Efekt do 2018 byl velmi silný na všech indexech. **Od 2019 je všude výrazně slabší** (US +0,23 R, Evropa +0,09 R) a pořád kladný.
  - To je hlavní riziko F33 na demu: mohlo by jít o efekt, který se ztrácí.
  - Proto platí sledování dopředu a vyhodnocení podle předem daných pravidel ([[F33 Rebalancování na konci měsíce|F33]]).
