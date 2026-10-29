---
tags: [od-uzivatele, export]
aktualizovano: 2026-10-29
---
# Export simulátoru za 2. den (2026-10-29)

`D:\Trading bot\scratch\exporty\simulator-data-2026-10-29.json` (data od 2026-10-27 15:00 do 2026-10-29 08:45 UTC).

| | |
|---|---|
| Účet | **89 331 $** (−10,7 % od startu; den 1 byl 96 147 $) |
| Uzavřeno | 46 obchodů, −10 636 $ – **všechno 1m ukázky** |
| `ukazka_ema_m1` | 27 obchodů, −4 835 $, win 30 % |
| `ukazka_m1` | 19 obchodů, −5 801 $, win 5 % |
| Otevřeno | 26 pozic: 24× [[Momentum L=250]], 1× BB squeeze, 1× 1m ukázka |
| [[Průraz F2 (proraz_d1)|Průraz F2]], [[RSI(2) pullback (mr_rsi2_d1)|RSI(2)]] | za 2 dny žádný signál (normální – ~1 za 5 dní / jen po výprodeji) |

**[[AI analytik]]**: z 65 hlasů 64× NE; signály s NE skončily v průměru **−0,88 R** → AI měla pravdu.
Zamítnuté [[Stínové obchody a verdikty|stínové]] 1m obchody dopadly stejně špatně jako vzaté → problém je strategie, ne filtr.

**Závěr:** 1m ukázky jen pálí účet (potvrzuje [[Náklady brokera]] a [[F2 Více timeframů|F2]]). Doporučení: v Nastavení
vypnout `ukazka_m1` a `ukazka_ema_m1` (vypíná uživatel), ať [[Učící režim]] sbírá data jen ze smysluplných systémů.
Exporty jsou platné, i když výzkum F7 není commitnutý – simulátor běží z nasazeného kódu, F7 aplikaci neměnil.
