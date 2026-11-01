---
tags: [infrastruktura, skill]
datum: 2026-10-30
---
# Day-trader skilly (trader-*)

Balík 11 skillů pro Claude od Jakeschincariol/day-trader-skill (MIT), prověřená verze commit `3d0f4ef`.
Nainstalováno 2026-10-30 do `C:\Users\korda\.claude\skills\trader-*`. Zdroj leží v `scratch/skill_src/day-trader-skill`.

## Co umí
- **scanner**: hledá US akcie (průraz 20denního high, bull flag, oversold, ORB na 5m).
- **news**: zprávy Yahoo a 8-K z SEC.
- **entry, exit**: ORB vstup, stop a cíl 2R.
- **timemachine**: replay a Monte Carlo z 60 dní 5m dat.
- **budget, risk**: velikost pozice a kontrola limitů.
- **broker**: tiket pro Alpaca/IBKR, paper jako výchozí, vždy až po výslovném „ano“.
- **alerts**: cenové alerty a hodiny NYSE.
- **analyst**: čísla z výkazů v SEC EDGAR.
- **pelosi**: obchody kongresmanů (House Clerk PTR).

## Prověrka (2026-10-30)
- Přečteny všechny skripty a SKILL.md.
- Jen standardní knihovna Pythonu, žádné eval/exec.
- Síť: pouze GET na veřejná data (Yahoo, Stooq, SEC, nasdaqtrader, House Clerk). Žádný POST, žádné odesílání dat.
- `ticket.py`, `size.py` a `check.py` nemají síť vůbec. Příkazy brokerovi jdou jen přes MCP Alpaca/IBKR, a to není nastavené.
- Zápisy jen do složky `trader/` v aktuálním projektu. ZIP z House Clerk se čte jen v paměti a nerozbaluje se na disk.
- Nemá `allowed-tools` ani skryté instrukce. Testy prošly: 315/315.

## Úpravy a omezení
- V nainstalovaných SKILL.md je `python3` nahrazené za `python`, protože `python3` je na tomto PC jen zástupce Microsoft Store.
- Jen US akcie, jen long. Na forex, zlato a indexy z [[Broker GlobalDynamicMarkets]] se nehodí.
- SEC nástroje (analyst, 8-K v news) potřebují `sec_user_agent` se jménem a e-mailem. Ten zadává uživatel sám.
- Signály skenneru nejsou ověřené. Jejich vlastní Time Machine příklad říká, že ORB je „close to a coin flip“, což sedí s [[Co nefunguje]].
- Broker ani klíče nenastavovat bez výslovného pokynu uživatele (viz [[Pravidla spolupráce]]).
