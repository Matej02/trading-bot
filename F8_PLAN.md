# F8 – strategie z FM PDF (S/D zóny na vyšších TF, daily bias, makro skóre)

Zadání uživatele (2026-10-29): „ať začne backtestovat a používat koncepty z PDF… hledání S/D zón na vyšších TF podle daných strategií, nebo live testovat“.
Pravidla jsou převzatá z vaultu `znalosti/FM/` (texty i všechny grafy PDF). **Plán je sepsaný před spuštěním**; varianty se vybírají jen na vývoji.

## Data a náklady
- MT5 H1 (server = Londýn), ~2009/2010–2026. Z H1 se skládají H4, D1 a W1. Den končí v 17:00 NY (jako futures a TradingView FX).
- Trhy s náklady v `simulator/lib/broker.json` (spread podle hodiny, swapy):
  - forex AUDJPY, AUDUSD, CADJPY, CHFJPY, EURCAD, EURJPY, EURUSD, GBPJPY, GBPNZD, GBPUSD, NZDJPY, NZDUSD, USDCAD, USDCHF, USDJPY;
  - kovy XAUUSD, XAGUSD;
  - indexy SPX500mini, NAS100mini, US30mini, GER_30mini, GBR_100mini, FRA_40mini, EUR_50mini;
  - ropa CRUDE_OIL, BRENT_OIL.
- Simulace: `f7_lib.sim_trade` na H1 (bid, long platí ask, limit se vyplní až průchodem o 1 tick, SL a TP ve stejné svíčce se počítá jako SL, swapy).
- **Vývoj do 2019-12-31, OOS od 2020-01-01.**

## Test A – S/D zóny (Hvězda, Šrajer, Valchář)
**Detekce zóny na TF (W1, D1, H4):**
- Pohyb ven = 1–3 svíčky stejného směru, součet těl ≥ k_out × ATR14 (k_out ∈ {1,5; 2,0}), první tělo ≥ 0,5 ATR.
- Báze = 1–6 malých svíček (tělo ≤ 0,5 ATR) těsně před pohybem ven.
- Demand: proximal = nejvyšší tělo báze, distal = nejnižší low báze a první svíčky pohybu ven. Supply zrcadlově.
- **Platnost:** do 5 svíček od začátku pohybu ven musí close prorazit poslední potvrzený swing high (pivot N=3), resp. low = BOS.
  Zóna je aktivní od tohoto close.
- **Pivotní** zóna = distal je extrém ±10 svíček (na swingu), jinak interní.
- **Jen první dotek:** limit na proximal. Zóna zaniká closem za distal.

**Varianty:**
- `A1 D` (Šrajer swing): D1 zóny, vstup limitem na D1 proximal.
- `A2 DvW` (Hvězda): D1 zóna, která se překrývá s platnou W1 zónou stejného typu.
- `A3 H4` (Šrajer/Valchář): H4 zóny.

Parametry k výběru na vývoji:
- pivot jen / vše;
- trendový filtr (2 vyšší high a 2 vyšší low pivotů N=3 na TF zóny) ano/ne;
- SL za distal / distal + 20 % (Hvězda);
- TP 2R / 3R / protější aktivní zóna (min 2R, max 6R; pod 2R se neobchoduje);
- BE při 1R ano/ne;
- k_out.

Maximální čekání na dotek je 120 svíček TF zóny, maximální držení 30 dní (D1/W1) nebo 10 dní (H4). Na jeden trh a směr nejvýš 1 otevřený obchod.

## Test B – Daily bias (Veselovský, Můčka)
Den t, signál ze svíčky t−1:
- **V:** close t−1 nad high t−2 → bull, cíl PDH. Sweep high t−2 a close pod ním → bear, cíl PDL. Pro low zrcadlově.
- **M:** býčí svíčka t−1 → cíl PDH, medvědí → cíl PDL.

Měří se:
1. Zásah cíle v den t proti nepodmíněné míře.
2. Obchod: vstup na open dne t ve směru biasu, TP = cíl, SL = opačný PD extrém, výstup na konci dne, s náklady.
   Srovnání s opačným a náhodným směrem.

## Test C – Makro skóre (Šrajer, Trading Analyzer CSV 2017–2024)
- Změna skóre ≥ 2 za 1 den (a varianta za 5 dní) → směr. Vstup na D1 close dalšího dne, kvůli neznámému času snímku.
- Výnos za 5, 10 a 20 dní v ATR, minus spread.
- Varianta bias: skóre ≥ +5 long, ≤ −5 short, rebalance denně.
- Vývoj 2017–2021, OOS 2022–2024-10.

## Prahy (jako F7)
- OOS: n ≥ 100, expektance ≥ 0,15 R, PF ≥ 1,3.
- Ziskové kvartály ≥ 60 %.
- O ≥ 0,1 R lepší než náhodné vstupy (stejný směr, stejná vzdálenost SL v ATR, stejné R cíle a doba).
- Plato kolem vybrané varianty.

## Live
Až něco projde, přidá se do simulátoru jako systém ve stínovém režimu (demo, zdarma) a bude se sledovat živě.

## Výsledky (2026-10-29) – detail ve vaultu `znalosti/Výzkum/F8 Strategie z FM PDF.md`
- **A (S/D zóny po FM):**
  - D1 OOS −0,22 R (n 255), H4 OOS −0,17 R (n 153), D v W málo obchodů. Náhodné vstupy −0,04 až −0,07 R.
  - Plato záporné, **neprošlo nic**.
  - První běh (+0,54 R) byl pohled do budoucnosti: aktivace před dokončením impulzu. Opraveno, viz `research_f8_kontrola.py` (test zpožděného vstupu).
- **B (daily bias):** zásah cíle 62–65 %, ale obchod −0,06 R. Opačný směr −0,17 R.
- **C (makro skóre):** změna o ≥ 2 body ani bias ±5 nemá výhodu (~0 ATR).
- **Závěr:** nic do bota ani do live testu.
