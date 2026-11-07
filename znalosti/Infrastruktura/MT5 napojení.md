---
tags: [infrastruktura, data]
aktualizovano: 2026-10-29
---
# MT5 napojení

`mt5_connector.py` se připojí k přihlášenému terminálu, heslo nikdy v kódu. Demo účet 937584 @ GlobalDynamicMarkets-Demo.
Terminál dá max 100 000 svíček (M1 ~3 měsíce, M15 ~4 roky) – pro delší M1 nastavit „Max. sloupců v grafu“ na neomezeně.
Historie má díry (EURUSD 10/2025–10/2026). Podmínky brokera: `export_broker_conditions.py` → [[Broker GlobalDynamicMarkets]].

**2026-11-07 – data MT5 a disk C:**
- Přesun `AppData\Roaming\MetaQuotes` na D přes odkaz (junction) **nefunguje**:
  - odkaz na celou složku → knihovna MetaTrader5 terminál nenajde;
  - odkaz na `bases` → MT5 ho odstraní, založí prázdné `bases` a chce přihlášení.
- **Místo toho promazaná mezipaměť historie:** zůstalo 13 trhů runneru, roky 2025+, bez tiků (0,8 GB). Na C se uvolnilo 21 GB.
- **Celá původní historie je jako záloha na `D:\MetaQuotes`.** Starší M1 MT5 kdykoliv stáhne znovu od brokera.

**2026-11-07 – čas serveru je UTC celý rok (bez letního času).** Kód (`research_f7_data`, `fetch_m1` v runneru) ho ale čte jako `Europe/London`. V britském letním čase (konec března až konec října) jsou proto časy M1 o **1 h dřív** než skutečnost. Doklad: otevření NY burzy je v datech v létě ve 12:30 místo 13:30 UTC; ověřeno i proti HistData ([[F13 indexy na delší historii (HistData 2010–2025)|F13 na delší historii]]). Testy i demo mají stejný posun, takže spolu sedí. Proti skutečnému času jsou ale v létě časová okna strategií posunutá o hodinu. Podle přání uživatele zatím neopraveno.

**2026-10-29:** „Max. sloupců v grafu“ = neomezeně (common.ini `MaxBars=100000000`) → M1 historie od 2017. Uloží se jen po potvrzení OK a restartu terminálu. Stažení: `python research_f7_data.py --mt5-m1` (od 2020, po rocích).
