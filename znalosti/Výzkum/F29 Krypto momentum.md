---
tags: [vyzkum, f29, krypto, momentum]
datum: 2026-11-07
---
# F29 Krypto momentum (4 týdny)

Z [[Fronta nápadů F22–F33|fronty nápadů]]. Jen test, bot se nemění. Skript `scratch/f29_krypto.py`.

## Plán (zapsán PŘED výpočtem)
**Pravidlo** (Liu a Tsyvinski 2021, momentum 1–4 týdny):
- Každé pondělí na otevření (00:00 UTC) long na týden, pokud byl výnos za posledních 28 dní > 0. Jinak mimo trh (long/flat).
- Popisně i varianta long/short.
- **Náklady:**
  - spread brokera relativně k ceně při každé změně pozice;
  - swap long za každou noc (krypto denně). BTC −0,0125 %/den, ETH **−0,10 %/den**.
  - U ostatních mincí náklady BTC (broker je nemá).

**Data:**
- **Vývoj:** Yahoo BTC 2014-09 až 2021-12 a ETH 2017-11 až 2021-12.
- **Kontrola:** Yahoo BTC+ETH 2022-01 až 2026-10.
- **Druhý zdroj:** Binance M1 → denní BTC+ETH 2022-09 až 2026-10.
- **Jiné trhy:** Binance XRP, LTC, ADA, BNB, DOGE, LINK, SOL 2022-09 až 2026-10.

**Srovnání:** stále long se stejnými náklady.

**Pravidla rozhodnutí (týdenní výnosy strategie včetně týdnů mimo trh, BTC a ETH průměrně), ANO jen když platí vše:**
1. Vývoj > 0 a t ≥ 2,0.
2. Kontrola > 0 a t ≥ 1,5.
3. Jiné mince (průměr) > 0.
4. Sharpe (průměr / sd týdenních výnosů) vyšší než stále long ve vývoji i v kontrole.
5. Druhý zdroj > 0.

## Výsledky (2026-11-07)
- Souhrn: `research_data/f29/f29_souhrn.txt`.
- **Swap ETH u brokera je −0,71 % za týden.** Při držení stále long to výnos ETH úplně sežere.

| Část | Momentum %/týden | t | Sharpe | Stále long Sharpe | V trhu |
|---|---|---|---|---|---|
| Vývoj Yahoo do 2021 | +1,84 | **4,07** | 1,51 | 1,18 | 59 % |
| Kontrola Yahoo 2022+ | +0,43 | **1,33** | 0,60 | −0,06 | 52 % |
| Druhý zdroj Binance 2022-09+ | +0,56 | 1,51 | 0,75 | 0,37 | 55 % |
| Jiné mince Binance | +0,49 | 1,15 | 0,57 | **0,59** | 49 % |

- V kontrole momentum vydělalo +113 %, stále long −59 %. Hlavně tím, že bylo mimo trh v propadu 2022 a mimo drahý swap ETH.
- **U ostatních mincí je momentum o něco horší než stále long** (Sharpe 0,57 vs 0,59).

**Rozhodnutí:** 1 ANO, **2 NE** (t 1,33 < 1,5), 3 ANO, 4 ANO, 5 ANO → **BEZ VÝHODY** podle pevných pravidel.
- **Nejblíž úspěchu ze všech testů.** Hranice se dodatečně neposouvá.
- Kandidát na sledování: jako filtr „být/nebýt v BTC a ETH“ pro simulátor (krypto běží 24/7). Jen po novém plánu předem a s novými daty.

## Live v simulátoru (od 2026-11-09, build db85757)
- Systém `f29_krypto_mom_d1` v `simulator/lib/f2x.ts`, kontrola shody `scripts/compare-f2x.ts` (358/358 nedělí).
- **Odchylky od testu:** vstup a výstup se každý týden zavírá a otevírá znovu (v testu se pozice při dalším long týdnu držela bez nákladů), SL 3 ATR jako pojistka.
- V registru Statistika: **unvalidated (kandidát)**.

## Live na MT5 demu (od 2026-11-09)
- `F29_krypto`, magic 20261129, BTCUSD a ETHUSD. Vstup v pondělí při první kontrole runneru (v testu 00:00 UTC). Viz [[FM live test na MT5 demu]].
- 9. 11.: mimo trh (BTC −10,6 %, ETH −16,2 %).
