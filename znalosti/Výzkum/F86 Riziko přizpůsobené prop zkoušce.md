---
tags: [vyzkum, f86, prop, riziko, plan]
datum: 2026-11-25
---
# F86 Riziko přizpůsobené prop zkoušce

Zadání uživatele (2026-11-25): „Ano, pokračuj bodem 1.“ (riziko přizpůsobené zkoušce, bez nových dat). Navazuje na [[Strategie výzkumu a měřítko prop zkoušky]] a [[F85 RSI(2) na akciích|F85]]. Bot se nemění.

**Proč:**
- Měřítko ukázalo, že F33 + RSI(2) s pevným rizikem 1 % projde zkouškou FTMO do 24 měsíců jen v 8 % startů (medián 31 měsíců).
- Při vyšším riziku rostou propady hlavně tehdy, když je otevřeno víc pozic na US indexech najednou (březen 2020).
- Otázka: dá se zkouška zkrátit jen tím, **kolik se riskuje a kdy**, beze změny obchodů?

## Plán (zapsán PŘED výpočtem)
**Obchody:** F33 (SPX, NAS) + RSI(2) (SPX, NAS, US30) přesně jako v měřítku (`scratch/prop_meritko.py`), pravidla FTMO 2 kroky stejná.

**Varianty** (r = základní riziko na obchod v % počátečního kapitálu):
| Varianta | Pravidlo |
|---|---|
| V0 | pevné riziko r (dnešní stav) |
| V1 | riziko klesá s propadem: r × min(1; (equity včerejšího zavření − 90) / 10). Při equity 95 % je to polovina. |
| V2 | strop otevřeného rizika 3 % (60 % denního limitu): nový obchod dostane min(r; 3 % − riziko otevřených pozic). Když zbývá méně než čtvrtina r, obchod se vynechá. |
| V3 | V1 a V2 dohromady |

- Riziko obchodu se určí při vstupu a dál se nemění. Více vstupů v jeden den má přednost v pořadí F33, pak RSI(2) SPX > NAS > US30.
- Mřížka r: 0,5 až 3,0 % po 0,25.

**Výběr a kontrola:**
- Vývoj = starty 2003–2014, kontrola = starty 2015–2023 (obsahují 2018, 2020 a 2022).
- U každé varianty se r* vybere **jen na vývoji**: nejvyšší r s podílem propadů ≤ 10 %.
- Hlavní číslo: **P24 = podíl startů, které projdou oběma fázemi do 24 měsíců.**
- Srovnávací bod: V0 při 1,0 % (dnešní bezpečné riziko z měřítka).

**Pravidla rozhodnutí (varianta pomáhá, jen když platí vše):**
1. Kontrola při r*: propadlo ≤ 10 %.
2. Celé období při r*: propadlo ≤ 10 %.
3. P24 aspoň o 10 p. b. vyšší než V0 při 1,0 %, a to ve vývoji i v kontrole zvlášť.

Když pomáhá víc variant, doporučí se ta s nejvyšším P24 v kontrole. **Popis navíc:** P12, P36, medián měsíců a V0 při r* vybraném na vývoji (jak by dopadlo pevné riziko vybrané na starších letech).

Skript `scratch/f86_riziko_zkousky.py`, výstup `research_data/prop/f86_souhrn.txt`.

## Výsledky (2026-11-25)
Výstup `research_data/prop/f86_souhrn.txt`. V0 při 1 % se shoduje s měřítkem (P24 8 %, P36 40 %, propadlo 0 %).

| Varianta | r* (vývoj) | Vývoj P24 / propadlo | Kontrola P24 / propadlo | Celé propadlo | Rozhodnutí |
|---|---|---|---|---|---|
| V0 pevné (srovnání při 1,0 %) | – | 4 % / 0 % | 12 % / 0 % | 0 % | – |
| V0 pevné, r vybrané na vývoji | 1,5 % | 38 % / 0 % | 45 % / **32 %** | 14 % | jen popis |
| V1 klesá s propadem | 1,75 % | 49 % / 6 % | 50 % / **27 %** | 15 % | NE (body 1, 2) |
| V2 strop otevřeného rizika 3 % | 1,75 % | 9 % / 0 % | 26 % / **36 %** | 15 % | NE (body 1–3) |
| V3 = V1 + V2 | 1,75 % | 7 % / 0 % | 26 % / **24 %** | 10 % | NE (body 1, 3) |

**Rozhodnutí: žádná varianta nepomáhá. Zůstává pevné riziko 1,0 %.**

**Proč (rozbor po výpočtu, jen popis):**
- Při 1,25 % propadlo 36 startů. **34 z nich v jediném měsíci, únoru 2020.** Tehdy byly otevřené F33 long SPX a NAS (vstup 26. 2.) a RSI(2) na NAS a SPX (vstupy 25. a 27. 2.) a trh padal několik dní za sebou.
- Denní limit FTMO se počítá ze zůstatku o půlnoci, ne z equity. Ztráta otevřených pozic z předchozích dnů se proto do limitu počítá celá a pád trvající několik dní ho prorazí i při stropu 3 %.
- F33 v testu nemá stop. 26. 2. 2020 šla SPX pozice na −2,18 R (low), runner na demu přitom používá stop 3 ATR (= −1 R).
- **Odhad propadů tedy stojí hlavně na jedné události.** Rok 2008 RSI(2) neobchodovala (indexy pod SMA200), takže nezávislých krachů s otevřenými pozicemi je v datech velmi málo. Proto je bezpečné jen riziko, které přežije únor 2020.

**Co z toho plyne:**
- Samotnou velikostí rizika se zkouška zkrátit nedá. Zkrátí ji jen víc výnosu z dalších nezávislých strategií.
- Další krok (jen návrh, s plánem předem): měřítko s F33 přesně tak, jak ji obchoduje runner (stop 3 ATR), protože simulace bez stopu je pro prop pesimistická.
