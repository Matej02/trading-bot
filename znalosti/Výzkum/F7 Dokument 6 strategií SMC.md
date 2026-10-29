---
tags: [vyzkum, neproslo]
aktualizovano: 2026-10-29
---
# F7 – 6 strategií z dokumentu uživatele (2026-10-28) → nic neprošlo

`F7_PLAN.md`, `f7_lib.py`, `research_f7*.py`. Dokument „Trading bot – 6 strategií (SMC + Volume Profile)“:
Sweep & Shift ([[SFP – sweep likvidity]] + [[MSS a displacement]] + [[FVG]]), zpřesněná [[Supply a demand zóny|S/D zóna]] (HVN),
rotace ve VA ([[Volume profile]], [[Režim trhu|balance]]), [[VWAP]] trend pullback, breakout z balance, [[Daily Open a Power of 3]].

Data: krypto M1 z Binance 2022–26 (9 mincí), forex/komodity z MT5 jen M15/M5 ([[Zdroje dat]]).
- Věrná pravidla: **< 1 obchod za rok na trh** (dokument tvrdil 1–5 týdně) – filtry se násobí.
- Uvolněné verze a ablace: ztrátové, horší než [[Náhodné vstupy|náhoda]].
- Koncepty na tisících událostí: SFP −0,03 R, VWAP pullback −0,03 R **i bez nákladů**.
Ověřeno [[Walk-forward|walk-forwardem]], Monte Carlem a kontrolou detekcí v grafu.

## Doplnění 2026-10-29: forex a komodity na M1
MT5 po nastavení neomezeného počtu svíček dal M1 od 2020 ([[MT5 napojení]]). EURUSD, GBPUSD, USDJPY, [[Zlato|zlato]], stříbro a ropa se vstupem M1–M15:
- Věrná pravidla: zase jen pár obchodů za rok. Žádná varianta nemá ani 30 obchodů ve vývoji.
- S1-jádro: forex −0,87 R (n 20), komodity −0,82 R (n 21). Pravidlo 80 % −0,53 až −0,71 R.
- Koncepty: SFP na všech poolech −0,01 až −0,51 R ve vývoji. [[VWAP]] pullback forex −0,16 R (n 450), komodity −0,03 R (n 458) → náznak u zlata z M15 zmizel.
**Závěr platí i pro [[Forex]] a komodity.**
