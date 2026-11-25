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

## Výsledky
(doplní se po výpočtu)
