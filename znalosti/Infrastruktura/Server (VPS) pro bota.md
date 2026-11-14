---
tags: [infrastruktura, vps, plan]
datum: 2026-11-14
---
# Server (VPS) pro bota (návrh, 2026-11-14)

Uživatel: „Budu to chtít dát na nějaký server. Řekni mi, kam to mám dát nejlevněji nebo zdarma, aby to bylo takhle funkční, jak je to teď.“

## Co dnes běží kde
| Část | Kde běží | Na serveru? |
|---|---|---|
| MT5 + runner `run_fm_demo.py` (demo) | PC uživatele | **ano**, hlavní důvod (PC se vypíná ve 20:00, F33 končí ve 21:55, F31 vstupuje ve 20:00) |
| Simulátor + bot 24/7 | Vercel + cron-job.org | ne, už běží na serveru zdarma |
| Úloha [[Pohled na grafy (automaticky)]] | Claude desktop na PC | volitelně: Claude desktop i na VPS, nebo zůstane na PC |
| Vault Obsidian | PC, git | zůstane na PC, synchronizace přes git |

## Požadavky
- **Windows.** Python balíček MetaTrader5 funguje jen na Windows. Linux s Wine je neoficiální a křehký, pro ARM ještě horší.
- **RAM:**
  - aspoň 4 GB pro Windows Server + MT5 + Python;
  - 8 GB, pokud tam má běžet i Claude desktop s úlohou grafů.
- Datacentrum v EU (Německo, Nizozemsko), měsíční platba bez dlouhého závazku.
- MetaQuotes VPS (hosting přímo v MT5) **nejde**, protože pouští jen MQL5 EA, ne Python runner.

## Možnosti (ceny z webu k 14. 11. 2026, před nákupem ověřit)
- **Zdarma nic spolehlivého:**
  - Azure free tier: 750 h měsíčně B1s / B2ats v2, ale jen 1 GB RAM. Na Windows + MT5 + Python je to málo. Podmínky (12 měsíců nebo „always“, disk P6 64 GB) se podle zdrojů liší.
  - AWS: od 15. 7. 2025 mají nové účty jen kredity (100–200 $) a Free plán končí uzavřením účtu.
  - Oracle Always Free: zdarma navždy, ale Linux/ARM, nebo AMD s 1 GB. Pro MT5 + Python nevhodné.
- **Nejlevnější použitelné: Windows VPS se 4–8 GB RAM, zhruba 10–16 $ měsíčně (asi 250–400 Kč):**
  - Contabo: nejvíc RAM za cenu, EU. Windows licence se platí zvlášť a celková cena je vidět až v košíku.
  - InterServer nebo Hostinger Windows: zhruba 10–11 $ za 4 GB, u Hostingeru licence v ceně.
- Specializované forex VPS (nízká latence k brokerovi) stojí zhruba 20–30 $ měsíčně. Pro naše strategie (držení hodiny až dny) nízká latence nerozhoduje.
- Bezplatné VPS od brokera bývá jen pro živé účty s vkladem nebo objemem. U demo účtu zřejmě ne.

## Doporučení
- Windows VPS s 8 GB RAM v EU za zhruba 10–16 $ měsíčně, např. Contabo Cloud VPS s Windows licencí. Pokud jen MT5 a runner, stačí 4 GB.
- **Postup:**
  1. Uživatel založí účet a zaplatí (Claude účty nezakládá a platby nedělá).
  2. Na VPS se připojí přes Vzdálenou plochu (RDP) a nainstaluje MT5 a Python 3.13. Přihlášení do MT5 si zadá sám.
  3. Claude připraví přesný návod a balíček souborů runneru (bez hesel a konfigurace účtu), start po spuštění Windows a kontrolu logu.
  4. Paralelní běh se nesmí stát: na PC runner vypnout, až poběží na VPS (jinak by obchodoval dvakrát).
  5. Úloha grafů: buď Claude desktop na VPS (8 GB), nebo zůstane na PC.
- Dopad na test: bot se nemění, jen místo běhu. Vyhodnocení 4. 1. 2027 platí dál.

Zdroje: [Azure free](https://azure.microsoft.com/en-in/free/dotnet), [Azure Q&A k free VM](https://learn.microsoft.com/en-us/answers/questions/5809104/unable-to-create-vms-in-any-region-for-this-size-u), [AWS Free Tier FAQ](https://aws.amazon.com/free/faqs/), [AWS free tier 2026](https://infratally.com/articles/aws-free-tier-2026/), [Windows VPS ceny 2026 (MassiveGRID)](https://massivegrid.com/blog/windows-vps-pricing-explained-licence-cost-cheapest-2026/), [Contabo Windows VPS blog](https://contabo.com/blog/windows-vps-rdp-affordable-guide/), [HostAdvice levné Windows VPS](https://hostadvice.com/vps/windows/cheap/).
