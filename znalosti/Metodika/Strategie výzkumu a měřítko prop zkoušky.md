---
tags: [metodika, prop, plan]
datum: 2026-11-25
---
# Strategie výzkumu a měřítko prop zkoušky (od 2026-11-25)

Zadání uživatele (2026-11-25): „Budu mít prop firmu… spíš nějakou challenge… jen jsem myslel, jestli nemůžeme na něčem zapracovat, třeba na strategii výzkumu atd., abychom to urychlili.“ Pak: „Ano, začni s tím, a pak mi dej výstup.“

Cíl: ostrý obchod jen přes prop zkoušku ([[Cesta k prop účtu]]), první volba FTMO 2 kroky ([[Prop firmy – doporučení]]). Malý účet se neřeší.

## 1. Pravidla FTMO 2 kroky (web FTMO, 25. 11. 2026)
- Cíl: **+10 %** (Challenge), pak **+5 %** (Verification), počítá se zůstatek se všemi pozicemi zavřenými.
- **Denní limit:** equity nesmí klesnout pod zůstatek o půlnoci SEČ/SELČ − 5 % počátečního kapitálu.
- **Celkový limit:** equity nesmí klesnout pod 90 % počátečního kapitálu (statický).
- Aspoň **4 obchodní dny** (dny s otevřeným obchodem) v každé fázi.
- **Bez časového limitu.** Neaktivita: FAQ uvádí riziko ukončení po 30 dnech bez obchodu (z [[Prop firmy – doporučení]], znovu ověřit).
- Akcie (CFD): 60 titulů (asi 45 USA, 15 Evropa), **páka u účtu Swing 1:1**, kontrakt 1 akcie, provize 0,004 % objemu, swap long např. AAPL −7,86 bodu/noc, obchodování USA 16:35–23:00 času serveru (15:35–22:00 Praha). Seznam: `research_data/f85/ftmo_akcie.txt`.

## 2. Měřítko prop zkoušky (zapsáno před výpočtem)
Každý kandidát se kromě prověrky (5 bodů) měří tím, **o kolik zkrátí zkoušku**.

**Simulace** (`scratch/prop_meritko.py`):
- Vstup: seznam obchodů (datum vstupu a výstupu, výsledek v R = jednotka rizika) a denní cesta obchodu (low a zavření v R), kde jsou denní data.
- Každá pozice riskuje stejné % počátečního kapitálu (bez skládání), souběžné pozice povolené.
- Den po dni: equity na zavření = zůstatek + otevřené pozice na zavření. **Nejhorší equity dne = zůstatek + všechny otevřené pozice na svém low** (pesimisticky, jako by všechny low nastaly ve stejnou chvíli).
- Propad = nejhorší equity pod denním limitem nebo pod 90 %.
- Fáze projde, když equity na zavření ≥ cíl a fáze má ≥ 4 dny se vstupem; otevřené pozice se zavřou za zavírací cenu. Fáze 2 začne další den od 100 %.
- Start každý měsíc 2003-01 až 2023-10, nejdéle 36 měsíců.
- **Neaktivita** se jen měří (podíl zkoušek, kde byla mezera > 30 dní bez vstupu), do výsledku se nepočítá.
- Rizika: 0,5 / 0,75 / 1 / 1,25 / 1,5 / 2 % na obchod.

**Hlavní číslo:** „bezpečné riziko“ = nejvyšší riziko s podílem propadů ≤ 10 %. U něj: prošlo do 12 / 24 / 36 měsíců a medián měsíců do projití obou fází.

**Kandidát pomáhá prop cíli**, když přidaný k portfoliu (dnes F33 + RSI(2)) při stejném riziku:
- zkrátí medián doby do projití aspoň o 20 % **nebo** zvýší podíl projití do 12 měsíců aspoň o 10 p. b.;
- a podíl propadů nepřekročí 10 %;
- obojí zvlášť pro starty 2003–2014 i 2015–2023.

To nenahrazuje prověrku: kandidát musí nejdřív projít svými 5 body a sledováním dopředu ([[Plán předem]]).

## 3. Postup testů (od F85)
- **Rychlé síto:** hrubá výhoda bez nákladů na vývojových datech. Když není ani hrubá výhoda (převis ≤ 0), plná prověrka se nedělá a test se zapíše jako NE.
- **Přísnější hranice:** od F35 je to ~50 testů, náhodou by prošly 1–2. Vývoj proto nově potřebuje **t ≥ 3,0** (dřív 2,0), kontrola t ≥ 2,0.
- **Nové zdroje výhody místo dalších variant na stejných trzích:** akcie (F85), později drift po výsledcích firem.

## Výsledky – výchozí stav (2026-11-25)
Výstup `research_data/prop/meritko_zaklad.txt`, skript `scratch/prop_meritko.py` (běží 5 s). 250 startů 2003–2023.

| Portfolio | Bezpečné riziko | Prošlo do 12 / 24 / 36 m | Propadlo | Medián do projití |
|---|---|---|---|---|
| RSI(2) samotná | 1,5 % | 2 % / 12 % / 40 % | 6 % | 27,8 měs. |
| F33 samotná | 1,25 % | 0 / 0 / 0 % | 0 % | – |
| **F33 + RSI(2)** | **1,0 %** | **0 % / 8 % / 40 %** | 0 % | **30,9 měs.** |

- F33 + RSI(2) při 1,25 %: prošlo do 36 m 65 %, ale propadlo 14 % (u startů od 2015 až 34 %, hlavně pád v březnu 2020, kdy jsou otevřené pozice RSI(2) i F33 zároveň).
- Při 2 %: medián 14 měsíců, ale propadne 59 %.
- **Neaktivita:** v 96–100 % zkoušek je mezera delší než 30 dní bez nového obchodu. Web FTMO (25. 11.): u CFD účtů FTMO po několika týdnech nečinnosti kontaktuje obchodníka a jde požádat o zmrazení. Pevné 30denní pravidlo našel jen u futures. Před nákupem ověřit u podpory.
- **Závěr:** s dnešními ověřenými strategiemi trvá zkouška FTMO typicky **2,5–3 roky** a do 12 měsíců neprojde skoro nikdy. Potřebujeme strategie s častějšími obchody, které nejsou svázané s pády indexů. To je cíl F85 a dalších testů. Kandidát se porovná s tímto řádkem podle pravidla výše.

## Testy podle měřítka
| Test | Prověrka | Měřítko při 1 % | Poznámka |
|---|---|---|---|
| [[F85 RSI(2) na akciích|F85]] RSI(2) na akciích | NE (1/5) | NE: medián 31 → 9 měs., ale propadlo 0 → 71 % | náklady CFD sežerou malou hrubou výhodu |
| [[F86 Riziko přizpůsobené prop zkoušce|F86]] riziko přizpůsobené zkoušce | NE (žádná varianta) | V1 až V3 v kontrole propadly 24–36 % | 34 z 36 propadů při 1,25 % v únoru 2020 |
| [[F87 Měřítko s F33 se stopem jako v runneru|F87]] F33 se stopem jako v runneru | korekce měřítka | **nový základ: bezpečné riziko 1,25 %, do 36 m 65 %, propadlo 3 %, medián 27 měs.** | stop F33 skoro nic nebere (−0,002 / −0,006 R) |
| [[F88 Drift po výsledcích firem (PEAD)|F88]] drift po výsledcích (akcie FTMO) | NE (3/6) | NE: propadlo 3 → 53 % | skutečný převis (t 3,7), ale menší než financování CFD |
| [[F89 Porovnání zkoušek FTMO 1 krok a 2 kroky|F89]] typ zkoušky FTMO | 2 kroky | 2 kroky při 1,25 %: P24 17 %, P36 65 %; 1 krok při 0,75 %: P24 10 %, P36 56 % | denní limit 3 % u 1 kroku moc těsný |
| [[F90 Denní pojistka na celý účet|F90]] denní pojistka na celý účet | NE (body 1 a 3) | M 1 % a 2,5 %: P24 66 %, ale kontrola propadlo 14 %, se skluzem 0,25 R 87 % | stojí na skluzu; odolná jen −3 % / 92 % při 1,5 % (P24 28–38 %, medián 24–25, dodatečně) |
| [[F91 Pravidla prop firem v měřítku|F91]] pravidla dalších firem | FTMO zůstává (The5ers neověřený denní limit) | The5ers Classic s denním 5 % při 1,25 %: P24 33 %, P36 76 %, medián 24,9; s 3 % jen 0,75 % a P24 5 %; Fintokei varování v 80 % zkoušek | cíl 8 % místo 10 % pomáhá; ověřit u The5ers denní limit a neaktivitu |
| [[F92 a F93 Výsledky firem během dne|F92]] den výsledků během dne | NE (3/6) | popis: propadlo 49 % při 1,25 % | t 1,4–1,6 |
| [[F92 a F93 Výsledky firem během dne|F93]] druhý den po výsledcích | **NE (5/6, jen pesimistické náklady)** | popis: F93 při 0,5 % + indexy 1,25 %: P24 62 %, propadlo 0 / 8 %, medián 19 | t 6,5 / 2,7, 23 z 23 let; rozhoduje skutečný spread akcií u FTMO |
| [[F94 až F96 Gap bez zprávy, náběh před výsledky, index a velké firmy|F94–F96]] gap bez zprávy, náběh před výsledky, NAS100 podle velkých firem | NE (3/6, 2/5, síto) | – | F94 jen do 2016, F95 ~0 po nákladech, F96 ani hrubě |
