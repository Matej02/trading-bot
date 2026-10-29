---
tags: [infrastruktura, agenti, ai]
aktualizovano: 2026-10-29
---
# AI analytik (Gemini)

Posoudí signál s kontextem: trend, RSI, spread vůči SL, příští zprávy, vyhlášená čísla a titulky ([[Zprávy a kalendář]]).
Záložní modely při přetížení (flash-latest → 2.5-flash → lite → 2.0-flash), 8 s na pokus.
Fronta: rozhodnutí hned, posudek AI se dopíše později (5 s mezi dotazy).
**Vysloužené veto**: NE se stane vetem až při ≥ 30 vyhodnocených ANO i NE, NE ztrátové a t ≥ 2 (`lib/aiScore.ts`).
Klíč GEMINI_API_KEY nastavuje uživatel ([[Pravidla spolupráce]]). Součást [[Agenti|agentů]].
