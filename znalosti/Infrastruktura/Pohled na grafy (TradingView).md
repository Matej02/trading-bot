---
tags: [infrastruktura, tradingview, grafy]
datum: 2026-11-11
---
# Pohled na grafy (TradingView)

Zadání uživatele (2026-11-11): „Potřebuju ještě vyřešit, abys reálně sledoval TradingView.“ Vybral variantu „ty se díváš na grafy“, ne alerty ani kontrolu signálů.

## Jak to běží
- **Naplánovaná úloha v aplikaci Claude** `pohled-na-grafy`, v pracovní dny v **8:05 (Londýn)** a **14:05 (New York)**.
  - Běží jen při otevřené aplikaci Claude. Když je zavřená, úloha se spustí při jejím příštím otevření.
  - Každý běh čerpá limit Claude uživatele.
- **Trhy** jako F13 na MT5 demu: EURUSD, GBPUSD, XAUUSD, NAS100, SPX500.
  - TradingView: OANDA:EURUSD, OANDA:GBPUSD, OANDA:XAUUSD, OANDA:NAS100USD, OANDA:SPX500USD.
- **Postup běhu:**
  1. `scratch/grafy_urovne.py` přečte z MT5 přesné úrovně: PDH/PDL, Asie 2–8, NY open a bias podle pravidel F13. MT5 jen čte a nespouští ho; když MT5 neběží, skončí.
  2. Claude otevře TradingView v prohlížeči aplikace **bez přihlášení**, u každého trhu denní graf a 15m.
  3. Napíše rozbor: bias, kde je cena vůči úrovním, co hlídat v killzone.
  4. Svůj bias zapíše se živou cenou (`grafy_urovne.py zapis TRH long/short/neutral`).
- **Výstup:**
  - denní poznámka `Grafy/Pohled na grafy RRRR-MM-DD.md`;
  - snímky v `Přílohy/Grafy/` (jen na disku, ne v gitu);
  - deník biasu `scratch/grafy/claude_bias.jsonl`.
- **Hranice:**
  - žádné přihlášení, hesla ani obchody na TradingView;
  - cookies odmítnout;
  - bot, runner ani MT5 se nemění a nespouští;
  - bez commitu a pushe, poznámky commituje hlavní relace při pondělní kontrole.

## Vyhodnocení (pravidla předem, 2026-11-11)
- `grafy_urovne.py vyhodnot` porovná každý zápis s koncem obchodního dne (17:00 NY):
  - **směr:** cena na konci dne vůči ceně při zápisu;
  - **cíl:** dosažení PDH (long) nebo PDL (short) do konce dne.
  - Stejně se hodnotí bias podle pravidel F13. Neutrální se nepočítá.
- **Rozhodnutí až po ≥ 30 obchodních dnech a ≥ 100 zápisech long/short.** Čtení grafu přidává hodnotu, jen když platí obojí:
  - směr Claude je lepší než 50 % se z ≥ 1,65;
  - a je lepší než bias pravidel.
- Do té doby rozbor **neovlivňuje bota ani simulátor**. Je to záznam pro výzkum, ne obchodní doporučení.
