---
tags: [vyzkum, f94, f95, f96, akcie, vysledky, plan]
datum: 2026-11-25
---
# F94 až F96 Gap bez zprávy, náběh před výsledky, index a velké firmy

Zadání uživatele (2026-11-25): „Pokračuj dalšími nápady F94–F96.“ Z [[Fronta nápadů F92–F96]]. Bot ani runner se nemění.

## Plán (zapsán PŘED výpočtem)
**Data:** výsledky z EDGAR (8-K 2.02, 40 firem, vyčištění jako [[F88 Drift po výsledcích firem (PEAD)|F88]]), denní ceny Yahoo akcií a NAS100. Vývoj 2004-09 až 2016, kontrola 2017–2026. Den reakce D jako v F88.

**F94 – gap bez zprávy (proti gapu, během dne):**
- U každé firmy jen dny od její první události v datech (u XOM, DIS, GOOG, AVGO chybí starší výsledky). Vyřazeny dny D−3 až D+3 kolem každé reakce na výsledky.
- Gap = otevření / včerejší zavření − 1. Gap trhu = medián gapů všech 40 akcií ten den (otevírací ceny indexu jsou 2004–2008 chybné).
- z = (gap − gap trhu) / směrodatná odchylka denních výnosů akcie za 60 dní.
- **|z| ≥ 2 → proti gapu**, otevření → zavření, stop 1 ATR(20).
- Náklady jako F92 (0,05 % + 0,004 % na stranu, pesimisticky 0,10 %), bez financování.

**F95 – náběh před výsledky (jen long):**
- X = poslední obchodní den před oznámením (= D − 1).
- **Long na otevření X − 4, výstup na zavření X (5 dní), výsledek se drží mimo pozici.** Stop 3 ATR(20).
- Náklady jako F88: půl spreadu 0,05 % + 0,004 % na stranu, financování 12 % ročně za noc. Pesimisticky 0,10 % a 15 %.

**F96 – NAS100 v den výsledků velkých firem:**
- Firmy Apple, Microsoft, Nvidia, Amazon, Meta, Alphabet. Jen oznámení před 9:30 nebo po 16:00 NY.
- Gap akcie v den D, z jako F92 (gap / směrodatná odchylka výnosů za 60 dní), |z| ≥ 2. Víc firem týž den → součet směrů, při nule bez obchodu.
- **NAS100 otevření → zavření ve směru gapu firmy**, stop 1 ATR(20) NAS100.
- Náklady: spread NAS100 od brokera (medián), pesimisticky dvojnásobek. Bez financování.

**Srovnání (všechny tři):** stejný obchod (stejný trh, směr, stop a délka) ve všech dnech období. Převis = R signálu − průměr. Vyhodnocení po dnech vstupu, t-test.

**Pravidla rozhodnutí, každý test zvlášť, ANO jen když platí vše:**
1. Síto: převis bez nákladů ve vývoji > 0.
2. Vývoj: R > 0, převis > 0, t ≥ 3,0.
3. Kontrola: R > 0, převis > 0, t ≥ 2,0.
4. Pesimistické náklady: R > 0 ve vývoji i kontrole.
5. Long i short převis > 0 (jen F94 a F96; F95 je jen long, bod odpadá).
6. Převis kladný aspoň v 60 % let.

**Při ANO:** [[Strategie výzkumu a měřítko prop zkoušky|měřítko prop zkoušky]] jako u F92 (nejvýš 3 akciové obchody denně, přednost |z|).

Skript `scratch/f94_f96.py`, výstup `research_data/f88/f94_f96_souhrn.txt`.

## Výsledky (2026-11-25)
Výstup `research_data/f88/f94_f96_souhrn.txt`.

| Test | Obchodů (vývoj / kontrola) | Vývoj: R / převis / t | Kontrola: R / převis / t | Body |
|---|---|---|---|---|
| F94 gap bez zprávy (proti gapu) | 302 / 434 | +0,089 / +0,141 / 2,30 | −0,011 / +0,042 / 0,77 | **3/6 – NE** |
| F95 náběh před výsledky (long 5 dní) | 1 524 / 1 521 | +0,014 / +0,022 / 1,38 | +0,027 / +0,030 / 1,78 | **2/5 – NE** |
| F96 NAS100 podle velkých firem | 123 / 100 | síto: převis bez nákladů −0,059 (t −1,06) | – | **NE (síto)** |

- **F94:** návrat po gapu bez zprávy byl do roku 2016 (t 2,3), od 2017 skoro zmizel (t 0,8).
- **F95:** malý náběh před výsledky existuje (převis +0,02 až +0,03 R), ale slabý a po nákladech ~0.
- **F96:** reakce velkých technologických firem nedává směr pro NAS100 během dne.
- **Rodina „akcie kolem výsledků během dne“:** z F92–F96 má skutečný efekt jen F93 (druhý den po reakci), viz [[F92 a F93 Výsledky firem během dne]].
