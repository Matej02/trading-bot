---
tags: [vyzkum, f60, indexy, denni-doba, nocni-drift]
datum: 2026-11-20
---
# F60 Noční drift US indexů při otevření Evropy

Zadání uživatele (2026-11-20): „Na nic nesahej, ale testuj dál…“ Jen test.

**Proč:**
- Boyarchenko, Larsen a Whelan (NY Fed, „The Overnight Drift“, 2020/2023): kladný noční výnos amerických akciových futures se soustředí hlavně do hodiny **02:00–03:00 New York**, kdy otevírá Evropa.
- [[F21 Noční drift indexů (long přes noc)|F21]] testovala celou noc (16:00 → 9:30) a profil po hodinách nepočítala. Tato hodina je proto nová, data o ní jsme neviděli.
- **Prakticky:** 02:00–03:00 NY = 08:00–09:00 Praha, kdy PC běží.

## Plán (zapsán PŘED výpočtem)
- **Pravidlo:** každý obchodní den (Po–Pá podle NY) long na otevření svíčky 02:00 NY, ven na zavření svíčky 02:59 NY (1 hodina). Bez SL a TP.
- **Náklady:** půl spreadu brokera podle hodiny (Londýn) na vstupu i výstupu. Swap ne, okno nepřechází půlnoc UTC.
- R = výsledek / ATR20 (denní, podle data v NY).
- **Srovnání:** stejná 1h pozice long ve všech ostatních celých hodinách dne (23 hodin). Převis = signál − srovnání, Welch t. Hodnotí se po dnech (průměr trhů).
- **Data:**
  - hlavní SPX500 a NAS100 z HistData M1 (skutečné UTC): vývoj 2010–2018, kontrola 2019–2025;
  - druhý zdroj H1 brokera 2019–2026 (SPX, NAS, US30);
  - jiné trhy DAX (HistData 2010–2025) a EuroStoxx (HistData 2010–2019), stejné okno 02:00 NY (= otevření Xetra).
- **Popis (nerozhoduje):** podmíněně podle toho, zda předchozí US seance (9:30–16:00) skončila dolů, nebo nahoru. Podle studie má být drift větší po poklesu.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Vývoj: signál > 0 a převis > 0 s t ≥ 2,0.
2. Kontrola: signál > 0 a převis > 0 s t ≥ 1,5.
3. Jiné trhy: převis > 0.
4. Broker 2019+: signál > 0 a převis > 0.
5. Převis kladný aspoň v 55 % let (HistData 2010–2025).

Skript `scratch/f60_evropa_drift.py`, výstup `research_data/f60/souhrn.txt`.

## Výsledky (2026-11-20)
Souhrn `research_data/f60/souhrn.txt`.

| Část | Signál R/den | Převis | t |
|---|---|---|---|
| Vývoj 2010–2018 (HistData SPX+NAS) | +0,004 | +0,009 | **3,96** |
| Kontrola 2019–2025 | −0,007 | −0,003 | −1,30 |
| Broker 2019–2026 | −0,005 | −0,001 | – |
| DAX + EuroStoxx | +0,004 (převis) | | |

- Převis kladný v 11 z 16 let, ale všechny záporné roky jsou od 2019.
- Po poklesu předchozího dne (jak píše studie): vývoj převis t 3,3, kontrola −0,8.
- **Rozhodnutí: body 2 a 4 NE ⇒ BEZ VÝHODY.** Jev byl silný do 2018 a od 2019 zmizel, stejně jako u F31 opačně, F38, F41, F48 a F59.
