---
tags: [metodika, naklady]
aktualizovano: 2026-10-29
---
# Náklady brokera

- Spread podle hodiny z [[Broker GlobalDynamicMarkets|brokera]] (`simulator/lib/broker.json`), long platí ask.
- EURUSD živě ~1,9 pipu (přirážka ~0,7 pipu na stranu), zlato ~0,6 $, BTC ~24 $, ETH 2,79 $.
- Swapy jako zlomek ceny za den, přirážka se platí oběma směry ([[Carry]], [[Momentum L=250]]).
- Rollover 21–22 UTC neobchodovatelný. 1m je neobchodovatelný (spread ~70 % SL).
- První chyba projektu: backtest bez spreadu, PF 1,22 → 0,69 ([[Metodické pasti]]).
