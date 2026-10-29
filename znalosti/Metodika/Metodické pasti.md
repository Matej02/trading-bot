---
tags: [metodika]
aktualizovano: 2026-10-29
---
# Metodické pasti

1. **Chybějící náklady** – PF 1,22 se po spreadu změnil na 0,69 ([[Náklady brokera]]).
2. **Překrývající se okna** – nafouknutá t-statistika ([[COT]]).
3. **Jednostranný test** – limitky vypadaly skvěle, druhá strana dala opak; byl to drift.
4. **Look-ahead** – pivot až po potvrzení, profil dne až po konci dne, RVOL jen z minulosti ([[F7 Dokument 6 strategií SMC|F7]]).
5. **Index datetime64[us]** v picklech – na sekundy přes `as_unit("s").asi8`, jinak obchody končí hned (chyba v [[F4 Vstup na menším timeframu|F4]]).
6. Netržní ceny v rolloveru vypadají jako edge ([[Time-of-day AUDJPY 23-00]]).

## Pohled do budoucnosti přes „kvalifikaci“ setupu (F8, 2026-10-29)
Setup se aktivoval po první svíčce impulzu, ale platnost se posuzovala i podle dalších svíček impulzu.
Vstup v té době pak „věděl“, že impulz pokračuje: H4 zóny vypadaly na +0,54 R a 85 % kladných kvartálů.
**Test: posunout vstup o 1 svíčku.** Když výhoda zmizí, jde o pohled do budoucnosti. Setup smí platit až po uzavření poslední svíčky, kterou používá.
→ [[F8 Strategie z FM PDF]]
