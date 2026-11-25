---
tags: [vyzkum, f88, akcie, pead, plan, prop]
datum: 2026-11-25
---
# F88 Drift po výsledcích firem (PEAD)

Zadání uživatele (2026-11-25): „Ano, pokračuj 1 a pak 2, ale na bota nesahej hlavně.“ Bot ani runner se nemění.

**Proč:**
- Jiný druh výhody než RSI(2): reakce na novou informaci, ne nákup po propadu. Mohla by být nezávislá na pádech indexů.
- Doloženo od Ball a Brown (1968) a Bernard a Thomas (1989): po silné reakci na výsledky cena často pokračuje stejným směrem.
- **Opatrnost předem:** Martineau (2022, „Rest in Peace Post-Earnings Announcement Drift“) uvádí, že u velkých firem drift od zhruba roku 2006 zmizel. Akcie FTMO jsou velké firmy, šance na úspěch je tedy spíš nízká.

## Plán (zapsán PŘED stažením dat a výpočtem)
**Data:**
- Data zveřejnění výsledků z registru EDGAR úřadu SEC: formulář 8-K s položkou 2.02 („Results of Operations“), čas přijetí.
- Ceny: Yahoo denní (už stažené v [[F85 RSI(2) na akciích|F85]]), index S&P 500 z Yahoo.
- **Vesmír:** americké akcie z nabídky FTMO, které podávají 8-K. Zahraniční firmy (BABA, ASML, AZN, RACE, ARM) podávají jiné formuláře a vypadnou.

**Událost a signál:**
- Den reakce D: přijetí 8-K před 9:30 NY = ten den; po 16:00 = další obchodní den; mezi tím = ten den.
- Jen formulář 8-K (ne 8-K/A). Další 8-K 2.02 do 20 dní od předchozí události se ignoruje.
- Reakce: AR = výnos akcie za den D − výnos indexu S&P 500 za den D (zavření D−1 → zavření D).
- z = AR / směrodatná odchylka denních nadvýnosů akcie za 60 dní před D−1.
- **z ≥ 2 → long, z ≤ −2 → short.** Vstup na otevření D+1, výstup na zavření 20. obchodního dne od vstupu.
- Stop 3 ATR(20) od vstupu (zásah přes low/high, při gapu za otevírací cenu). R = výsledek / 3 ATR.
- **Náklady:** půl spreadu 0,05 % a provize 0,004 % na stranu, financování 12 % ročně za noc pro long i short (swap FTMO je záporný oběma směry). Pesimisticky 0,10 % a 15 %.

**Srovnání:**
- U každé akcie a směru se spočítá průměrné R stejného obchodu (vstup na otevření, 20 dní, stop 3 ATR) ve **všech** dnech daného období.
- Převis obchodu = R − tento průměr. Vyhodnocení po dnech vstupu, t-test průměru převisu.

**Období:** vývoj 2004-09 až 2016 (položka 2.02 existuje od srpna 2004), kontrola 2017–2026.

**Pravidla rozhodnutí, ANO jen když platí vše:**
1. Síto: převis bez nákladů ve vývoji > 0 (jinak NE a dál se nepočítá).
2. Vývoj: R signálu > 0, převis > 0, t ≥ 3,0.
3. Kontrola: R signálu > 0, převis > 0, t ≥ 2,0.
4. Pesimistické náklady: R signálu > 0 ve vývoji i kontrole.
5. Obě strany: převis longů > 0 i převis shortů > 0 (celé období).
6. Převis kladný aspoň v 60 % let.

**Popis (nerozhoduje):**
- počty událostí a obchodů;
- prahy z 1,5 a 3 a držení 10 a 40 dní;
- korelace měsíčních výsledků s RSI(2) na indexech;
- [[Strategie výzkumu a měřítko prop zkoušky|měřítko prop zkoušky]] při 1,25 %: základ F33 se stopem + RSI(2) ([[F87 Měřítko s F33 se stopem jako v runneru|F87]]) proti základ + F88. Nejvýš 5 akciových pozic, přednost nejvyšší |z|.

Skripty `scratch/f88_stahni.py`, `scratch/f88_pead.py`, výstup `research_data/f88/souhrn.txt`.

## Výsledky (2026-11-25)
**Data:**
- EDGAR, 3 305 podání 8-K 2.02, po vyčištění 3 050 událostí u 40 firem (2004-09 až 2026-11), 59 MB v `research_data/f88/raw`.
- SEC vyžaduje kontakt v hlavičce User-Agent. Použit e-mail uživatele s jeho výslovným souhlasem (25. 11.), zadaný jen při spuštění, v repozitáři se neukládá.
- U XOM, DIS, GOOG a AVGO chybějí roky před změnou čísla firmy v EDGAR. Ochrana soukromí aplikace další stahování s e-mailem zablokovala, takže zůstaly jen novější roky.

**Ověření:** časy přijetí jsou UTC (Apple 16:30 NY = 21:30 Z v zimě), převedeny na čas New Yorku.

| Část | Obchodů | R signálu | Převis nad stejnými obchody ve všech dnech | t |
|---|---|---|---|---|
| Síto: vývoj bez nákladů | 855 | +0,109 | +0,117 | 3,47 |
| Vývoj 2004–2016 | 855 | **−0,029** | +0,121 | 3,70 |
| Kontrola 2017–2026 | 879 | **−0,046** | +0,068 | 1,96 |

- Pesimistické náklady: −0,075 / −0,087 R.
- Long převis +0,066, short +0,098. Převis kladný v 19 z 23 let.
- **Rozhodnutí: 3/6 bodů → NEPROŠLO.**
- **Proč:** drift po výsledcích u akcií FTMO existuje (převis t 3,7 a v 83 % let kladný), ale je menší než náklady držení akciových CFD. Financování ~12 % ročně za 20 dní a spread stojí asi 0,14 R na obchod, hrubý zisk je +0,11 R.

**Popis:**
- držení 10 dní: kontrola převis +0,061 (t 2,29), ale R ≈ 0;
- prahy 1,5 a 3: podobně;
- korelace s RSI(2) +0,10 (nezávislé);
- **měřítko při 1,25 %:** propadlo 53 % (základ 3 %). Ztrátové obchody zkoušku jen pokazí.

**Poučení:** u akciových CFD na prop účtu sežere vícedenní akciové strategie financování. Efekt by mohl fungovat jen se skutečnými akciemi bez swapu, to ale na prop účtu nejde.
