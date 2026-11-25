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

## Výsledky
(doplní se po výpočtu)
