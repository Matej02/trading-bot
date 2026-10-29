---
tags: [koncept, databaze]
aktualizovano: 2026-10-29
---
# Databáze konceptů

Cíl (uživatel 2026-10-29): podrobně popsané trading koncepty z materiálů **FM** a z dokumentů,
aby z nich šlo skládat a testovat strategie. Každý koncept = jedna poznámka podle [[Šablona konceptu]].

## Stav
- **FM část 1** (Základy + strategie 9 mentorů, 314 PDF) je zpracovaná 2026-10-29, přehled v [[FM materiály]].
  Každý koncept má sekci „Z materiálů FM“ nebo z FM rovnou vznikl. **Část 2 dodá uživatel.**
- Mechanické definice z [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]] jsou v sekcích „Definice z dokumentu“.

## Koncepty
| Koncept | Skupina | Zdroje | Otestováno |
|---|---|---|---|
| [[Market structure]] | struktura | FM všichni | jen jako součást F7 |
| [[MSS a displacement]] | SMC / struktura | dokument, FM | F7 |
| [[Supply a demand zóny]] | SMC | dokument, **FM (jak kreslit, TF)** | F5, F7, **F8 (D1/H4/W1 po FM) – bez výhody** |
| [[Order block]] | SMC | dokument, FM | F5 |
| [[FVG]] (iFVG, BPR) | SMC | dokument, FM | F5, F7 |
| [[Likvidita]] (ERL/IRL) | SMC | dokument, FM | F5, F7 |
| [[SFP – sweep likvidity]] | SMC / likvidita | dokument, FM | F5, F7 – bez výhody |
| [[Premium a discount]] | SMC / kontext | FM | F7 (filtr) |
| [[Support a rezistence]] (balanční levely) | price action | FM | ne |
| [[Horizontální levely]] (M/W/D, opens) | price action | FM | částečně (D open) |
| [[Trendline a kanály]] | price action | FM | ne |
| [[Fibonacci a golden pocket]] | price action | FM | F7 (OTE) |
| [[Svíčkové formace]] | price action | FM | ne |
| [[Elliottovy vlny]] | price action | FM | ne (subjektivní) |
| [[Volume profile]] | objem | dokument, FM | F5, F7 |
| [[VWAP]] | objem | dokument, FM | F7 |
| [[Futures data a objem]] | objem / data | FM | – (omezení dat) |
| [[Killzones a session]] | čas | dokument, FM | F7 |
| [[Daily Open a Power of 3]] | čas | dokument, FM | F5, F7 |
| [[Daily bias]] | čas / kontext | FM | **F8 – náklon směru, obchod −0,06 R** |
| [[Režim trhu]] | kontext | dokument, FM | F7 |
| [[COT]] | fundament | v1–v6, FM | v1–v6 |
| [[Makro skóre měn]] | fundament | FM + **data skóre 2017–2024** | **F8 – bez výhody** |
| [[Sezónnost]] | fundament | FM | ne |
| [[DXY a dolar]] | fundament | FM | ne |
| [[Mean reversion]] | styl | vlastní | F1, F6 – funguje jen indexy |
| [[Trend following]] | styl | vlastní | F2, F3, F6 |
| [[Turn-of-month]] · [[Carry]] | jiné | vlastní | F1, v1–v6 |

## Jak se z toho budou dělat strategie
Kombinace konceptů → [[Plán předem]] → test na datech ([[Výběr, kontrola, holdout]], [[Náhodné vstupy]]).
Pozor: čím víc kombinací, tím víc „vítězů“ náhodou. Proto oddělené ověřovací období a korekce na počet testů.
Hotové kombinace od mentorů FM (entry modely) jsou v poznámkách ve [[FM materiály]], seřazené podle testovatelnosti.
