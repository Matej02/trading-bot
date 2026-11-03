---
tags: [infrastruktura, agenti]
aktualizovano: 2026-10-29
---
# Agenti

| Agent | Hlídá | Váha |
|---|---|---|
| Validátor | čerstvost, utečená cena, duplicita | veto |
| Trh teď | víkend, rollover, spread | veto |
| Kalendář | zprávy 30 min před / 15 po ([[Zprávy a kalendář]]) | veto |
| Risk | limity a velikost ([[Risk management]]); od 2026-11-03 i SL aspoň 3× spread od vstupu | veto |
| Statistik | jen ověřené setupy (`lib/registry.json`) | radí / veto |
| Ďáblův advokát | důvody proti | radí |
| [[AI analytik]] | Gemini posudek | radí, veto až si ho vyslouží |

Každé rozhodnutí se zpětně vyhodnotí ([[Stínové obchody a verdikty]]). Starší verze v Pythonu: [[Python bot tv_agent]].
