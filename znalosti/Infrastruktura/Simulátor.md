---
tags: [infrastruktura]
aktualizovano: 2026-10-29
---
# Simulátor (webová aplikace)

Next.js 16 na Vercelu: https://trading-bot123-fawn.vercel.app – nasazuje se pushem na GitHub `Matej02/trading-bot` (main, kořen `simulator`).
Graf jako TradingView, simulovaný broker s podmínkami MT5 ([[Broker GlobalDynamicMarkets]]), data na serveru v Upstash Redis.
Strategie převedené 1:1 z Pythonu (`lib/strategies.ts`, kontrola shody s Pythonem).
Části: [[Agenti]], [[AI analytik]], [[Zprávy a kalendář]], [[Bot 24-7]], [[Učící režim]], [[Stínové obchody a verdikty]], [[Zdroje dat]].

## Experiment F9 (2026-10-29)
Systémy `fm_mss_h4`, `fm_pruraz_h4`, `fm_zona_h4` (`lib/fm.ts`): kombinace FM konceptů, signál na zavření H4, TP 3R, 21 trhů. NEOVĚŘENO, jen live sběr dat. Viz [[F9 Kombinace FM konceptů]].
