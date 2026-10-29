---
tags: [od-uzivatele, dokument]
aktualizovano: 2026-10-29
---
# Dokument „Trading bot – 6 strategií (SMC + Volume Profile)“

Poslal uživatel 2026-10-28. Originál: ![[Trading bot – 6 strategií (SMC + Volume Profile).pdf]]
(též `.docx` v [[Přílohy]]; text i v `D:\Trading bot\scratch\docx\strategie.txt`).

## Obsah
- Předpoklady: kontext H4/H1, setup M15, vstup M1–M15 přes [[MSS a displacement|MSS s displacementem]]; časy v NY ([[Killzones a session]]).
- Trhy: EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD, WTI, BTC, ETH, SOL; volume = tick volume z MT5.
- Stavební bloky: pivoty, struktura/BOS/MSS, displacement, RVOL, [[FVG]], [[Order block]], [[Supply a demand zóny]],
  [[Likvidita]], [[SFP – sweep likvidity|SFP]], [[Volume profile]], [[VWAP]], [[Daily Open a Power of 3|Daily Open]], [[Režim trhu]].
- 6 strategií: Sweep & Shift, zpřesněná S/D zóna, rotace ve Value Area, VWAP trend pullback, breakout z balance přes LVN,
  Daily Open manipulace (Power of 3).
- [[Risk management]]: 0,5 % na obchod, denní −2R, týdenní −5R, max 3 pozice, korelace, zprávy ±30 min.
- Postup testování: vizuální kontrola, bez look-ahead, M1 filly, 60/40 + [[Walk-forward]], [[Náhodné vstupy]], ablace, Monte Carlo.
  Prahy: n ≥ 100, expectancy ≥ 0,15 R, PF ≥ 1,3, DD95 ≤ 15 R, ziskové kvartály ≥ 60 %.

## Výsledek testu
Otestováno v [[F7 Dokument 6 strategií SMC]] → **nic neprošlo**. Věrná pravidla < 1 obchod/rok/trh (dokument odhadoval 1–5 týdně).
Kontrola detekcí: ![[f7_kontrola_detekci_BTCUSD.png]]

## Připomínka uživatele (2026-10-29)
S/D zóny podle dokumentu „hledá na špatných TF, moc malé“ → uživatel popíše, jak je kreslí sám (doplnit do [[Supply a demand zóny]]).
