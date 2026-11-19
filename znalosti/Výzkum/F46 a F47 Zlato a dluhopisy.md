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
