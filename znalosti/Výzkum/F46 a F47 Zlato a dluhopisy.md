---
tags: [vyzkum, f46, f47, zlato, dluhopisy]
datum: 2026-11-19
---
# F46 a F47 Zlato a dluhopisy

Zadání uživatele (2026-11-19): „Ano, pokračuj testy na zlato a dluhopisy. Všechno tohle dávej klidně na Vercel, tam to můžeme testovat, co a jak. Do bota bych dával fakt jen to, u kterého je velká šance na úspěch.“

Dluhopisy broker nenabízí (žádné bondové CFD), proto slouží jen jako **signál** pro zlato. Jen test, bot se nemění. Data: broker H1 XAU/XAG 2009–2026, Yahoo XAU od 2000, Yahoo TLT od 2003 (`research_data/f33/yahoo`). Nic se nestahuje.

## F46 Zlato v asijské seanci (plán PŘED výpočtem)
- **Proč:** u zlata se popisuje, že roste hlavně v asijských hodinách a v americké seanci spíš klesá (fyzická poptávka v Asii, prodeje v USA).
- **Pravidlo:** každý obchodní den long XAU od 23:00 do 07:00 Londýn (8 h). Čas brokera s posunem +1 h v britském letním čase jako v `f2x_lib`.
- **Náklady:** spread brokera podle hodiny vstupu a výstupu. Swap se neplatí (vstup po rolloveru 22 UTC, výstup před dalším).
- R = výsledek / ATR20 denního rozpětí.
- **Srovnání (drift):** stejně dlouhé 8h okno long ve všech ostatních začátcích hodin (0–22 h Londýn). Rozhoduje převis.
- **Data:** vývoj broker H1 2009–2018, kontrola broker H1 2019–2026. Jiný trh: stříbro XAG (celé období). Druhý zdroj není (HistData XAU se nestahuje), proto přísnější bod 5.
- **ANO jen když platí vše:**
  1. Vývoj: > 0, převis > 0, t ≥ 2,0.
  2. Kontrola: > 0, převis > 0, t ≥ 1,5.
  3. Stříbro: převis > 0.
  4. Po nákladech kladné i v nejhorší třetině let.
  5. Převis kladný aspoň v 60 % let.

## F47 Dluhopisy → zlato (plán PŘED výpočtem)
- **Proč:** zlato nenese úrok, takže když klesají výnosy dluhopisů (TLT roste), zlato bývá silnější. Test, jestli se to dá využít **předem**.
- **Pravidlo:** na zavření posledního obchodního dne měsíce: výnos TLT za měsíc > 0 → long XAU celý další měsíc (zavření → zavření), jinak mimo trh.
- **Náklady:** spread při vstupu a výstupu, swap long za noci.
- **Test:** průměrný měsíční výnos zlata po měsících s TLT nahoru − po měsících s TLT dolů (Welch t). Plus Sharpe strategie proti stále long zlato.
- **Data:** vývoj Yahoo 2003–2018, kontrola Yahoo 2019–2026, druhý zdroj broker XAU 2019–2026. Jiný trh: stříbro (Yahoo).
- **ANO jen když platí vše:**
  1. Vývoj: rozdíl > 0, t ≥ 2,0.
  2. Kontrola: rozdíl > 0, t ≥ 1,5.
  3. Stříbro: rozdíl > 0.
  4. Broker 2019+: rozdíl > 0.
  5. Sharpe strategie > stále long zlato, ve vývoji i v kontrole.

Skript `scratch/f46_f47.py`, výstup `research_data/f46/souhrn.txt`.

## Výsledky (2026-11-19)
Souhrn `research_data/f46/souhrn.txt`, skript `scratch/f46_f47.py`.

**F46 Zlato v asijské seanci:**

| Část | n dní | R/den | Ostatní okna | Převis | t |
|---|---|---|---|---|---|
| Vývoj 2009–2018 | 1793 | +0,018 | −0,018 | **+0,036** | **5,10** |
| Kontrola 2019–2026 | 936 | +0,020 | 0,000 | +0,019 | 2,03 |

- Stříbro: převis +0,004 (samotné −0,088 R).
- Po letech: kladné 16 z 18 let, převis kladný 17 z 18. Nejhorší třetina let −0,001 R.
- **Podle hodiny začátku okna:** okna od 18 do 23 h Londýn kladná, okna od 2 do 17 h záporná. Zlato roste večer a v noci, v londýnské a newyorské seanci klesá.
- **Bod 4 NE (−0,001, o vlásek) ⇒ BEZ VÝHODY** podle pravidel předem.
- **Nejbližší kandidát ze všech testů:** statisticky silný a stálý, ale na obchod malý (+0,02 ATR denně). Na stříbře se neopakuje.
- Podle pravidla uživatele: na MT5 ne. Do simulátoru na Vercel jen jako sledování dopředu, pokud uživatel chce.

**F47 Dluhopisy → zlato:**
- Vývoj: rozdíl +0,48 p. b. za měsíc, t 0,65. Kontrola: +0,31 p. b., t 0,33.
- Sharpe strategie v kontrole 0,63 proti 0,82 u stále long.
- **⇒ BEZ VÝHODY.** Měsíční směr dluhopisů nepředpovídá zlato.
