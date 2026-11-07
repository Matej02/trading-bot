---
tags: [strategie, kandidat]
aktualizovano: 2026-10-29
---
# RSI(2) pullback (`mr_rsi2_d1`)

- Long, když denní zavření > SMA200 a RSI(2) < 10. Ven při zavření nad SMA5, stop 3 ATR(20), nejdéle 10 dní, **bez TP**.
- Jen [[US indexy]] (SPX500mini, NAS100mini, US30mini).
- Úspěšnost **71–73 %**, průměrná výhra +0,35–0,41 R, ztráta −0,51–0,54 R → skutečné RR ~1:0,65–0,8.
  Plný stop jen v ~12 % obchodů, nejhorší −1,4 R (gap). Průměr +0,11–0,14 R na obchod.
- Z [[F6 Denní strategie]], formálně neprošel (kontrola 2019–23 slabá). V [[Simulátor|simulátoru]] neověřený → obchoduje v [[Učící režim|učícím režimu]].
- **2026-11-07 ([[F24 Filtr volatility pro živé strategie|F24]]):** kladná v klidném i nervózním trhu. Vývoj do 2018 +0,093 R (n 599), kontrola 2019+ +0,118 R (n 218). Filtr volatility nepomáhá.
- Typ: [[Mean reversion]]. Opak profilu [[Průraz F2 (proraz_d1)|průrazu]] (málo velkých výher).
