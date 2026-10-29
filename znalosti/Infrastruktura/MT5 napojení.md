---
tags: [infrastruktura, data]
aktualizovano: 2026-10-29
---
# MT5 napojení

`mt5_connector.py` se připojí k přihlášenému terminálu, heslo nikdy v kódu. Demo účet 937584 @ GlobalDynamicMarkets-Demo.
Terminál dá max 100 000 svíček (M1 ~3 měsíce, M15 ~4 roky) – pro delší M1 nastavit „Max. sloupců v grafu“ na neomezeně.
Historie má díry (EURUSD 10/2025–10/2026). Podmínky brokera: `export_broker_conditions.py` → [[Broker GlobalDynamicMarkets]].

**2026-10-29:** „Max. sloupců v grafu“ = neomezeně (common.ini `MaxBars=100000000`) → M1 historie od 2017. Uloží se jen po potvrzení OK a restartu terminálu. Stažení: `python research_f7_data.py --mt5-m1` (od 2020, po rocích).
