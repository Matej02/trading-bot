---
tags: [infrastruktura, data]
aktualizovano: 2026-10-29
---
# Zdroje dat

| Zdroj | Na co | Poznámka |
|---|---|---|
| Yahoo Finance | denní historie od 1970, živé svíčky v simulátoru | `range=max` vrací měsíční svíčky – použít period1/period2 |
| Binance | krypto živě, M1 historie (data.binance.vision) | skutečný objem |
| [[MT5 napojení|MT5]] | tick volume, náklady brokera | limit 100 000 svíček, díry |
| ForexFactory / FXStreet | [[Zprávy a kalendář]] | FXStreet historii bez webové hlavičky nevydá |
| Dukascopy | – | automatické stahování odmítá (429), nepoužívat |

Od 2026-10-29 dává [[MT5 napojení|MT5]] M1 od 2017 (neomezený počet svíček).
