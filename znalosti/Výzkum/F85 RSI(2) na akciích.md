---
tags: [vyzkum, f85, akcie, rsi2, plan, prop]
datum: 2026-11-25
---
# F85 RSI(2) na akciích

Zadání uživatele (2026-11-25): „Ano, začni s tím, a pak mi dej výstup.“ (nová strategie výzkumu a akcie u prop firmy, [[Strategie výzkumu a měřítko prop zkoušky]]). Bot se nemění.

**Proč:**
- [[F42 RSI(2) přísná prověrka|RSI(2)]] funguje na US indexech, ale dává jen ~17 dní vstupu ročně. Na akciích by stejné pravidlo dávalo stovky obchodů ročně, takže statistika i sledování dopředu by trvaly měsíce, ne roky.
- Krátkodobý návrat k průměru u jednotlivých akcií je doložený v literatuře (Jegadeesh 1990, Lehmann 1990; Connors a Alvarez pro RSI(2)).
- FTMO nabízí 60 akciových CFD (asi 45 USA, 15 Evropa), páka u Swing 1:1 ([[Strategie výzkumu a měřítko prop zkoušky]]).

## Plán (zapsán PŘED stažením dat a výpočtem)
- **Pravidlo beze změny proti F42** (žádné nové parametry):
  - signál na zavření dne, kdy zavření > SMA200 a RSI(2) < 10;
  - vstup na otevření dalšího dne;
  - výstup na zavření dne, kdy zavření > SMA5, nejdéle 10. den;
  - stop 3 ATR(20) od vstupu (přes low dne, při gapu za otevírací cenu);
  - jedna pozice na titul, nový vstup až po výstupu.
- **Srovnání (drift):** stejné vstupy a výstupy ve všech dnech, kdy je titul nad SMA200, bez podmínky RSI. Rozhoduje převis signál − srovnání.
- **Vesmír pro vývoj a kontrolu:** členové S&P 500 **k danému dni** (historické složení indexu), titul se obchoduje jen ve dnech, kdy byl v indexu. Tím se nepoužije dnešní seznam vítězů.
- **Data:** Yahoo denní, upravené o splity a dividendy. Historické složení S&P 500 z veřejného seznamu na GitHubu (fja05680/sp500).
- **Náklady:** půl spreadu 0,05 % na vstupu i výstupu, provize 0,004 % na stranu, financování 12 % ročně za každou noc (přiblížení swapu FTMO). R = výsledek / 3 ATR.
- **Vyhodnocení po dnech vstupu** (průměr titulů, které ten den vstupují), jako u F42.
- **Období:** vývoj 1996–2018, kontrola 2019–2026.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s **t ≥ 3,0** (přísnější hranice, [[Strategie výzkumu a měřítko prop zkoušky|od F85]]).
2. Kontrola: signál > 0 a převis > 0 s t ≥ 2,0.
3. Pesimistické náklady (2× spread, financování 15 % ročně): signál > 0 ve vývoji i kontrole.
4. Evropské akcie z nabídky FTMO (Yahoo, celé období): převis > 0.
5. Převis kladný aspoň v 60 % let.

**Rychlé síto:** když je převis ve vývoji bez nákladů ≤ 0, další body se nepočítají a výsledek je NE.

**Popis (nerozhoduje):**
- pokrytí daty: podíl členů indexu, které Yahoo má, po letech (zaniklé firmy chybí a výsledek vylepšují);
- americké akcie z nabídky FTMO 2019–2026 (dnešní seznam, proto jen popis);
- výstup až na otevření dalšího dne (provoz bez serveru);
- korelace měsíčních výsledků s RSI(2) na indexech;
- [[Strategie výzkumu a měřítko prop zkoušky|měřítko prop zkoušky]]: portfolio F33 + RSI(2) + F85, nejvýš 5 akciových pozic najednou (páka 1:1), při více signálech přednost nejnižší RSI(2).

Skript `scratch/f85_rsi2_akcie.py`, výstup `research_data/f85/souhrn.txt`.

## Výsledky (2026-11-25)
Souhlas se stažením: „Ano, stáhni to a spusť test.“ Výstup `research_data/f85/souhrn.txt`, skripty `scratch/f85_stahni.py` a `scratch/f85_rsi2_akcie.py`. Parita výpočtu s F42 na SPX: 481/481 obchodů, rozdíl 0.

**Data:**
- složení S&P 500: 2 720 změn, 1996-01-02 až 2026-08-18, 1 209 tickerů;
- Yahoo má data jen pro 737 z nich (zaniklé a převzaté firmy chybí);
- pokrytí členů: 1996 38 %, 2005 53 %, 2015 72 %, 2026 98 %. Chybějící firmy výsledek spíš vylepšují.

| Část | Obchodů | Signál R | Srovnání | Převis | t |
|---|---|---|---|---|---|
| Síto: vývoj bez nákladů | 48 115 | +0,033 | +0,019 | +0,014 | 2,95 |
| Vývoj 1996–2018 | 48 115 | −0,003 | −0,007 | +0,004 | 0,89 |
| Kontrola 2019–2026 | 24 304 | −0,011 | −0,012 | +0,001 | 0,15 |
| Evropa FTMO (13 titulů) | 2 512 | −0,003 | −0,011 | +0,009 | 0,83 |

- Pesimistické náklady: vývoj −0,023 R, kontrola −0,031 R.
- Převis kladný v 18 z 31 let (58 %).
- **Rozhodnutí: 1/5 bodů → NEPROŠLO.** Bez nákladů je u akcií jen malá hrubá výhoda (+0,033 R na obchod) a náklady akciových CFD (spread, provize, financování 12 % ročně) ji celou spotřebují.

**Popis:**
- americké akcie FTMO 2019–2026: signál −0,009 R, převis −0,002;
- výstup na otevření dalšího dne: ještě horší (−0,006 / −0,013 R);
- korelace s RSI(2) na indexech +0,47 (padá ve stejných měsících);
- **měřítko prop zkoušky:** F85 přidaná k F33 + RSI(2) při 1 % zkrátí medián na 9 měsíců, ale **propadne 71 % zkoušek** (základ 0 %). To je jen hazard, žádná výhoda.
- Páka 1:1 by při 1 % riziku byla v 14 % dní překročená.

**Poučení:** RSI(2) funguje na indexech, ne na jednotlivých akciích po nákladech CFD. Krátkodobý návrat u velkých akcií je po roce 2000 slabý (shoda s literaturou o slábnoucím short-term reversal).
