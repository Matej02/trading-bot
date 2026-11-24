---
tags: [vyzkum, plan, forex, intradenni]
datum: 2026-11-24
---
# F71 a F72: londýnský průraz a víkendový gap na měnách

Zadání uživatele (2026-11-24): „Ano, pokračuj výzkumem.“ Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč tahle rodina:**
- Kalendářní jevy od 2019 mizí, návrat k průměru funguje jen na US indexech denně ([[F42 RSI(2) přísná prověrka|F42]]).
- Na měnách jsme testovali drift v místních hodinách ([[F58 a F59 Měny v místních hodinách a Turnaround Tuesday|F58]]), fixing ([[Fronta nápadů F35–F39|F35]]), gotobi (F48), RSI(2) (F54) a carry (F1). **Průraz asijského rozpětí a víkendový gap jsme netestovali.**
- Obojí jsou známé obchodní nápady z praxe, v literatuře se slabou oporou. Proto přísná pravidla.
- Data máme: H1 brokera pro měny od 2010 (`research_data/{pár}_H1.pkl`, čas UTC; díry 10/2025–2/2026 a 6–8/2026 nevadí) a M1 HistData 2010–2025 pro EURUSD, GBPUSD, USDJPY (`research_data/histdata/m1_fx`, UTC).
- Náklady: spread brokera z `research_data/naklady.json` (pole `naklad`, cena za celý obchod). Intradenní obchody bez swapu.

## F71 Londýnský průraz (průraz asijského rozpětí)
- **Asijské rozpětí:** high a low svíček 00:00–07:00 Londýn (7 hodinových svíček), pracovní dny. Musí být všech 7.
- **Vstup:** stop příkaz na high rozpětí (long) a low rozpětí (short), platí 07:00–12:00 Londýn. Bere se jen první průraz (druhý se ruší).
- **Stop** na druhé straně rozpětí, **cíl** 1× rozpětí od vstupu, jinak **výstup v 16:00 Londýn** za zavírací cenu.
- **R** = šířka rozpětí. Den se vynechá, když je rozpětí menší než 5× spread (náklad by byl přes 20 % R).
- **H1 (broker):** když se ve stejné svíčce dotkne obou stran rozpětí → ztráta −1 R. Ve svíčce vstupu se počítá jen stop, ne cíl. Když svíčka zasáhne stop i cíl → stop. (Konzervativně.)
- **M1 (HistData):** stejné, jen s minutovým pořadím.
- **Hlavní trhy:** EURUSD a GBPUSD. **Jiné trhy:** USDJPY, EURJPY, GBPJPY, AUDUSD, EURGBP, USDCHF, USDCAD, NZDUSD, AUDJPY, EURCHF.
- **ANO jen když platí vše:**
  1. Vývoj (broker H1 2010–2018, hlavní trhy): čistý průměr R > 0, t ≥ 2,0.
  2. Kontrola (broker H1 2019–2026, hlavní trhy): čistý průměr R > 0, t ≥ 1,5.
  3. Druhý zdroj (HistData M1 2010–2025, EURUSD a GBPUSD): čistý průměr R > 0.
  4. Jiné trhy (broker 2010–2026): průměr všech > 0 a kladných aspoň 6 z 10.
  5. Kladný čistý výsledek aspoň v 55 % let (hlavní trhy, broker).

## F72 Víkendový gap na měnách (návrat ke zavření v pátek)
- **Gap** = otevírací cena první svíčky nového týdne − zavírací cena poslední svíčky pátku. **ATR20** z denních svíček (dny UTC) k pátku.
- **Signál:** |gap| ≥ 0,25 ATR20.
- **Vstup proti gapu** na otevření první svíčky týdne. **Cíl** = páteční zavření (zavření gapu), **stop** = stejná vzdálenost na druhou stranu (1:1). Jinak výstup po 24 hodinách (zavření 24. hodinové svíčky).
- **R** = |gap|. **Náklad** 3× spread (v neděli večer je spread široký). Swap za jednu noc se zanedbá (méně než 1 pip).
- Svíčka se stopem i cílem → stop.
- **Hlavní trhy:** 12 párů EURUSD, GBPUSD, USDJPY, EURJPY, GBPJPY, AUDUSD, EURGBP, USDCHF, USDCAD, NZDUSD, AUDJPY, EURCHF.
- **Jiné trhy:** XAUUSD, XAGUSD, EURAUD, EURCAD, GBPAUD, GBPCAD, AUDCAD, AUDNZD, NZDJPY, CADJPY.
- **ANO jen když platí vše:**
  1. Vývoj (broker H1 2010–2018, hlavní trhy dohromady): čistý průměr R > 0, t ≥ 2,0.
  2. Kontrola (broker 2019–2026): čistý průměr R > 0, t ≥ 1,5.
  3. Druhý zdroj (HistData M1 2010–2025, EURUSD, GBPUSD, USDJPY): čistý průměr R > 0.
  4. Jiné trhy (broker 2010–2026): průměr > 0 a kladných aspoň 55 % trhů.
  5. Kladný čistý výsledek aspoň v 55 % let.

## Výsledek
(doplní se po výpočtu)
