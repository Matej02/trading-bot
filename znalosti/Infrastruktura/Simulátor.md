---
tags: [infrastruktura]
aktualizovano: 2026-10-29
---
# Simulátor (webová aplikace)

Next.js 16 na Vercelu: https://trading-bot123-fawn.vercel.app – nasazuje se pushem na GitHub `Matej02/trading-bot` (main, kořen `simulator`).
Graf jako TradingView, simulovaný broker s podmínkami MT5 ([[Broker GlobalDynamicMarkets]]), data na serveru v Upstash Redis.
Strategie převedené 1:1 z Pythonu (`lib/strategies.ts`, kontrola shody s Pythonem).
Části: [[Agenti]], [[AI analytik]], [[Zprávy a kalendář]], [[Bot 24-7]], [[Učící režim]], [[Stínové obchody a verdikty]], [[Zdroje dat]].

## Experiment F12 (2026-11-03)
- Systém `fm12_mucka_m1` (`lib/fm12.ts`): Můčka podle PDF a [[Doplňující pravidla k FM PDF|doplňujících pravidel]].
  - Vstup na 1m, 4H a denní svíčky z 1h, zóny a balanční levely z 15m. Bot mu načítá více timeframů (`htf` v definici systému).
  - Trhy EURUSD, GBPUSD, XAUUSD, XAGUSD. NAS100 ne, protože Yahoo dává jen hodiny burzy.
  - Limit na 0,618 je živě vstup trhem na 1m svíčce, která úroveň zasáhne.
  - NEOVĚŘENO, jen live sběr dat. Viz [[F12 Můčka podle doplňujících pravidel]].
- Shoda TS/Python: `scripts/compare-f12.ts` + `scratch/f12_parita.py`.
- Veřejný `/api/tick/status` ukazuje `build` (commit nasazené verze) – kontrola, že se push nasadil.

## Oprava 2026-11-03: stop uvnitř spreadu
- [[Agenti|Risk]] vetuje obchod, když je SL od vstupu blíž než 3× spread, nebo na špatné straně.
- 1m ukázky dávaly na BTC stop 3–7 $ při spreadu ~24 $ a ztrácely −10 až −18 R. Za týden to bylo −56 786 $ z −60 061 $ (281 obchodů).
  Viz [[Export simulátoru 2026-11-03]].

## Experiment F9 (2026-10-29)
Systémy `fm_mss_h4`, `fm_pruraz_h4`, `fm_zona_h4` (`lib/fm.ts`): kombinace FM konceptů, signál na zavření H4, TP 3R, 21 trhů. NEOVĚŘENO, jen live sběr dat. Viz [[F9 Kombinace FM konceptů]].
