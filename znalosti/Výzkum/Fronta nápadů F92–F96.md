---
tags: [vyzkum, fronta, prop, akcie]
datum: 2026-11-25
---
# Fronta nápadů F92–F96 (2026-11-25)

Zadání uživatele (2026-11-25): „Ano, pokračuj, dej mi seznam nápadů.“ Cíl: nová nezávislá strategie s **častějšími obchody**. Zrychlí prop zkoušku a vyřeší 30denní neaktivitu u FTMO ([[F91 Pravidla prop firem v měřítku|F91]]).

## Co už je vyčerpané (nenavrhovat znovu)
- Kalendář na indexech: konec a začátek měsíce, OPEX, svátky, Halloween, FOMC, ECB, NFP/CPI, dny v týdnu.
- Intradenní indexy a měny: ORB, gap, momentum první a poslední půlhodiny, noční drift, otevření Evropy, londýnský průraz.
- Návrat k průměru (RSI(2)) na indexech, kovech, měnách, kryptu, ropě a akciích.
- Momentum a průrazy, signály z jiných trhů (VIX, dluhopisy, jen), páry, carry, SMC a FM.
- Vícedenní akciové obchody: financování CFD ~12 % ročně je sežere ([[F85 RSI(2) na akciích|F85]], [[F88 Drift po výsledcích firem (PEAD)|F88]]).

## Proč akcie během dne
- Obchod otevřený a zavřený týž den neplatí financování, jen spread a provizi (~0,11 % tam a zpět).
- [[F88 Drift po výsledcích firem (PEAD)|F88]] ukázal, že po výsledcích firem cena u akcií FTMO opravdu pokračuje (převis +0,12 R za 20 dní, t 3,7, kladný v 83 % let). Vícedenní držení ale stojí víc, než vynese.
- Pro prop účet ideální: žádná ztráta přes noc, takže žádné „hromadění“ floating ztráty jako v únoru 2020. Výsledky firem se nekryjí s pády indexů.
- Data už máme: 3 050 výsledků 40 firem z EDGAR (2004–2026) a denní ceny z Yahoo. Nic se nestahuje.
- **Omezení pro živý provoz:** obchoduje se 15:30–22:00 Praha, runner by musel běžet do 22:00 (VPS). Sledování dopředu jde v simulátoru z denních dat (otevření → zavření).

## Nápady
| # | Nápad | Pravidlo (návrh) | Obchodů ročně | Odhad šance |
|---|---|---|---|---|
| **F92** | Den výsledků během dne | Den reakce na výsledky: gap otevření proti včerejšímu zavření ≥ 2σ (očištěný o index) → vstup na otevření ve směru gapu, výstup na zavření, stop 1 ATR | ~60–80 | **~15 %** |
| **F93** | Druhý den po výsledcích | Den po dni reakce (z ≥ 2 jako v F88): otevření → zavření ve směru reakce, stop 1 ATR | ~60–80 | ~10 % |
| F94 | Gap bez zprávy na akciích | Gap ≥ 2σ očištěný o index, v den bez výsledků → proti gapu, otevření → zavření | ~150+ | ~8 % |
| F95 | Náběh před výsledky | Long 5 dní před oznámením, výstup na zavření den před oznámením (bez rizika gapu z výsledků) | ~150 | ~5 % |
| F96 | Index v den výsledků velkých technologických firem | NAS100 otevření → zavření ve směru reakce Apple, Microsoft, Nvidia, Amazon, Meta, Alphabet | ~24 | ~5 % |

**Odhad šance** je hrubý. Od F35 prošly přísnou prověrkou 2 z ~55 testů (~4 %). F92 a F93 mají vyšší šanci, protože navazují na efekt, který F88 našel, a odstraňují to, co ho zabilo (financování).

## Postup (stejný jako dosud)
- Plán předem, rychlé síto (hrubá výhoda ve vývoji), vývoj t ≥ 3,0, kontrola t ≥ 2,0, pesimistické náklady, obě strany (long i short).
- Pak [[Strategie výzkumu a měřítko prop zkoušky|měřítko prop zkoušky]]: o kolik zkrátí zkoušku a kolik vyplní 30denních mezer.
- Bot se nemění. Do simulátoru až se souhlasem uživatele.
