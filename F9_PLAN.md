# F9 – kombinace FM konceptů (koncepty pevné, strategie se skládají)

Zadání uživatele (2026-10-29):
- Koncepty z FM PDF zůstávají, strategie se mění („ať si kutí“).
- Kombinovat popsané věci.
- Otestovat, nasadit do simulátoru na webu a commitnout pro live test.

## Formát přenositelný do simulátoru
- Signál na **zavření H1 svíčky**, vstup trhem. SL podle konceptu, TP = **2R** (výchozí RRR simulátoru), maximální držení 48 H1 svíček.
- Kontext (den, H4, Asie) se skládá z H1 a stačí mu **1 000 svíček** (limit Binance pro krypto).
- Čas dne v NY. Obchodní den 17:00–17:00 NY.

## Stavební bloky (koncepty z vaultu `znalosti/Koncepty`)
**Spouštěče (T):**
1. `sweepPD`: SFP na PDH/PDL. Knot za úrovní, close zpět; první v daný den.
2. `sweepAsia`: SFP na high/low Asie (20–02 NY) během 02–12 NY.
3. `mss`: do 12 svíček po sweepu (PD nebo Asie) close za high/low, ze kterého šel pohyb do sweepu. SL za extrém sweepu.
4. `fvg`: dotek 50 % H1 FVG (≥ 0,3 ATR, ne starší než 24 svíček) a close ve směru.
5. `ob`: retest H1 order blocku (poslední opačná svíčka před BOS) s close ve směru.
6. `zona`: dotek H4 S/D zóny po FM (F8) s **potvrzovací svíčkou** (close ve směru, Hvězda).
7. `prurazPivot`: close za posledním H1 pivotem N=3 (Pátek).
8. `balance`: retest proraženého H4 pivotu (S/R flip) s close ve směru.

**Filtry (F):**
- `trendD1`: struktura D1, 2 vyšší high a 2 vyšší low.
- `trendH4`: struktura H4.
- `emaD1`: close nad EMA20 D1.
- `biasV`, `biasM`: daily bias podle Veselovského a Můčky.
- `discount`: cena ve spodní polovině 10denního range pro long.
- `kz`: killzone 02–05 nebo 08–11 NY.
- `nyDO`: long pod NY open 00:00.
- `zonaH4`: uvnitř aktivní H4 zóny stejného směru.

**Kombinace:** 8 T × (0–2 filtry z 9 = 46) × TP 1,5/2/3R = 1 104.

## Metodika
- 28 trhů (26 z F8 + BTC, ETH), náklady brokera.
- **Výběr na 2010–2017**: exp > 0, t > 2, n ≥ 100.
- **Validace 2018–2021**: exp ≥ 0,10 R, t > 2.
- **Holdout 2022–2026 jednou**, plus náhodné vstupy.
- Na trh a kombinaci nejvýš 1 otevřený obchod.
- Kontrola pohledu do budoucnosti: vstup o 1 svíčku později nesmí výhodu zničit.
- Do simulátoru jdou kombinace, které projdou validací. Holdout a live jsou pak skutečné ověření.
  V simulátoru jsou označené jako **experiment F9** se svými čísly.

## Výsledky (2026-10-29) – detail ve vaultu `znalosti/Výzkum/F9 Kombinace FM konceptů.md`
- 2 208 kombinací (H1 i H4 základ): **0 prošlo výběrem 2010–17** (exp > 0, t > 2; náhodou by se čekalo ~25), 0 kladných i ve validaci.
- Do simulátoru jako **live experiment (NEOVĚŘENO)** jdou 3 nejlepší H4 kombinace podle vývoje: `fm_mss_h4`, `fm_pruraz_h4` a `fm_zona_h4`.
  TP 3R, 21 trhů. Shoda TS/Python 119/120 signálů (`simulator/scripts/compare-fm.ts`).
