---
tags: [vyzkum, f90, prop, ftmo, riziko, plan]
datum: 2026-11-25
---
# F90 Denní pojistka na celý účet

Zadání uživatele (2026-11-25): „Ano, začni bodem 1 a pak 2.“ Bod 1 = pojistka, bod 2 = pravidla dalších firem ([[F91 Pravidla prop firem v měřítku|F91]]). Bot ani runner se nemění, jen simulace.

**Proč:**
- V [[F86 Riziko přizpůsobené prop zkoušce|F86]] stálo 34 z 36 propadů na únoru 2020. Několik pozic na US indexech je otevřených najednou a denní limit FTMO (equity pod zůstatkem o půlnoci − 5 %) přeskočí i floating ztráta z předchozích dnů.
- Pojistka zavře všechny pozice, když equity spadne na úroveň kousek nad limitem FTMO. Ze špatného dne je ztráta, ne propadnutá zkouška.
- V F86 se netestovala (testovalo se jen klesající riziko a strop otevřeného rizika).
- **Riziko:** pojistka zavírá na dně propadu a RSI(2) vydělává právě na odrazu, takže může ubrat zisk.

## Plán (zapsán PŘED výpočtem)
**Obchody:** základ měřítka F33 se stopem + RSI(2) ([[F87 Měřítko s F33 se stopem jako v runneru|F87]]), zkouška FTMO 2 kroky ([[F89 Porovnání zkoušek FTMO 1 krok a 2 kroky|F89]]), starty každý měsíc 2003-01 až 2023-10, nejdéle 36 měsíců.

**Pojistka:**
- Limit FTMO dne: L = max(zůstatek o půlnoci − 5 %, 90 %) počátečního kapitálu.
- Pojistka zavře všechny otevřené pozice, když equity klesne na **L + M**. Rezerva M = **0,5 / 1,0 / 1,5 / 2,0 %**. Jedním parametrem tak chrání denní i celkový limit (M = 1 → denně −4 %, celkově 91 %).
- **Gap na otevření:** když už equity na otevírací ceně pozic držených z minulých dnů ≤ L + M, zavře se za otevírací cenu. Když je přitom pod L, zkouška propadla.
- **Jinak:** když nejhorší equity dne (všechny pozice na svém low zároveň, jako v měřítku) ≤ L + M, zavře se na L + M minus skluz.
- **Skluz:** 0,1 R za každou otevřenou pozici (asi 0,3 ATR, ~1 % pohybu indexu při krachu). Citlivost 0,25 R. Když skluz dostane equity pod L, zkouška propadla.
- Zavřené pozice se neotevírají znovu, další obchody strategií běží normálně od dalšího dne.
- Otevírací cena je z denních dat indexu (cash). CFD se obchoduje i přes noc, kde by pojistka zasáhla dřív, takže je to pesimistické.

**Riziko:** pevné 0,5–4,0 % na obchod po 0,25.

**Kontrola shody:** bez pojistky musí výsledek odpovídat F87 a F89 (1,25 %: P24 17 %, P36 65 %, propadlo 3 %, medián 27,2).

**Výběr jen na vývoji (starty 2003–2014):**
- pro každé M: r_vývoj(M) = nejvyšší riziko s propady ≤ 10 % ve vývoji;
- M* = nejvyšší P24 ve vývoji při r_vývoj(M) (při shodě kratší medián).

**Pravidla rozhodnutí, ANO jen když platí vše (při M* a r* z vývoje):**
1. Propadlo ≤ 10 % ve vývoji i v kontrole (starty 2015–2023).
2. Ve vývoji i v kontrole zvlášť proti základu bez pojistky při 1,25 % (ve stejné části): medián do projití kratší aspoň o 20 % **nebo** P12 vyšší aspoň o 10 p. b. (kritérium měřítka z [[Strategie výzkumu a měřítko prop zkoušky]]).
3. Se skluzem 0,25 R propadlo ve vývoji i v kontrole ≤ 15 %.

**Popis (nerozhoduje):**
- celé období pro všechna M a rizika;
- kolikrát pojistka zasáhla a ve kterých dnech;
- financovaný účet 12 měsíců po projití s pojistkou.

**Co by ANO znamenalo:** pravidlo pro runner na prop účtu (zavedení jen na pokyn uživatele). Pojistka funguje, jen když runner běží celý americký obchodní den (15:30–22:00 Praha) i přes noc. Dnes se PC vypíná v 19:47, takže na prop by byl potřeba VPS ([[Cesta k prop účtu]], krok 5).

Skript `scratch/f90_pojistka.py`, výstup `research_data/prop/f90_souhrn.txt`.

## Výsledky (2026-11-25)
Výstup `research_data/prop/f90_souhrn.txt`. Bez pojistky se shoduje s F87 (1,25 %: P24 17 %, P36 65 %, propadlo 3 %, medián 27,2).

**Výběr na vývoji:** M* = 1,0 % (denně −4 %, celkem 91 %), r* = 2,5 %.

| Při M* = 1 %, r* = 2,5 % | P12 | P24 | Propadlo | Medián |
|---|---|---|---|---|
| Vývoj 2003–2014 | 29 % | 75 % | 2 % | 13,8 měs. |
| Kontrola 2015–2023 | 24 % | 54 % | **14 %** | 14,8 měs. |
| Kontrola se skluzem 0,25 R | 11 % | 13 % | **87 %** | 7,0 měs. |
| Základ bez pojistky 1,25 %, kontrola | 6 % | 22 % | 7 % | 25,1 měs. |

- Bod 1 (propadlo ≤ 10 % i v kontrole): **NE** (14 %, propady v srpnu 2015 a v říjnu 2020).
- Bod 2 (medián −20 % nebo P12 +10 p. b.): ANO.
- Bod 3 (skluz 0,25 R): **NE** (propadlo 81 % / 87 %).
- **Rozhodnutí: NEPROŠLO.**

**Proč:** pojistka funguje, jen když se pozice zavřou rychle a skoro bez skluzu. Při vyšším riziku je otevřených víc korelovaných pozic na US indexech najednou a skluz se sčítá. Při 0,25 R na pozici přeskočí limit FTMO i s pojistkou. Při M* a r* pojistka zasáhla ve 347 různých dnech, je to tedy běžný mechanismus, ne výjimka.

**Financovaný účet:** s pojistkou při 2,5 % přežije 12 měsíců jen 85 % (bez pojistky při 1,25 % 100 %).

**Dodatečný popis po výsledku (nerozhoduje, `research_data/prop/f90_popis.txt`):**
| Varianta | Skluz 0,1 R | Skluz 0,25 R |
|---|---|---|
| M = 2 % (denně −3 %, celkem 92 %), 1,5 % | P24 38 %, medián 23,6, propadlo 0 / 0 % | P24 28 %, medián 24,9, propadlo 0 / 0 % |
| M = 2 %, 1,75 % | P24 48 %, medián 20,9, propadlo 0 / 0 % | propadlo 0 / **20 %** |
| M = 1,5 %, 1,75 % | P24 53 %, medián 19,9, propadlo 0 / 0 % | propadlo **32 / 33 %** |

(propadlo vývoj / kontrola)
- Jediná varianta odolná na skluz: **pojistka −3 % denně a 92 % celkem při riziku 1,5 %**. P24 se zvedne ze 17 % na 28–38 %, medián se ale zkrátí jen z 27 na 24–25 měsíců. Je to vybrané až po výsledku, takže to není ověřené.
- Skutečný skluz se z denních dat určit nedá. Rozhodne až simulace na minutových datech (HistData SPX a NAS od 2010, MT5 od 2017), kde je vidět skutečná cesta cen všech pozic najednou. To je samostatný test, jen se souhlasem uživatele.

**Poučení:** pojistka je nutná ochrana pro prop runner (dodatečně odolná varianta −3 % / 92 % nic neubrala), ale **zkoušku výrazně nezrychlí**. Vyšší riziko s pojistkou stojí na kvalitě exekuce, kterou z denních dat neověříme. Pojistka navíc potřebuje runner běžící celý den i noc (VPS).
