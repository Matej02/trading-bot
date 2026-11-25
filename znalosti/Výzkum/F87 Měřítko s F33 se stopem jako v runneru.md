---
tags: [vyzkum, f87, prop, f33, plan]
datum: 2026-11-25
---
# F87 Měřítko s F33 se stopem jako v runneru

Zadání uživatele (2026-11-25): „Ano, pokračuj 1 a pak 2, ale na bota nesahej hlavně.“ **Bot ani runner se nemění**, jde jen o výzkumný výpočet.

**Proč:**
- Test [[F33 Rebalancování na konci měsíce|F33]] nemá stop.
- Runner na demu ji ale obchoduje se stopem 3 ATR(20) z denních dat ([[FM live test na MT5 demu]]).
- [[F86 Riziko přizpůsobené prop zkoušce|F86]]: 34 z 36 propadů zkoušky v únoru 2020, kdy pozice F33 na SPX šla na −2,18 R. **Měřítko tedy F33 nemodeluje tak, jak by se na prop účtu opravdu obchodovala.**

## Plán (zapsán PŘED výpočtem)
- **F33 se stopem:**
  - stejné vstupy a výstupy jako test;
  - navíc stop 3 ATR(20) od vstupu (long pod, short nad);
  - zásah přes low/high dne, při gapu přes stop za otevírací cenu;
  - náklady obchodu stejné jako v testu (rozdíl test − hrubý výsledek na zavření).
- **Popis F33:** průměrné R se stopem a bez stopu, 2003–2018 a 2019–2026, počet zastavených obchodů.
- **Měřítko:** F33 se stopem + RSI(2), pevné riziko 0,5–3,0 % po 0,25, stejná simulace jako v [[Strategie výzkumu a měřítko prop zkoušky|měřítku]]. Vývoj = starty 2003–2014, kontrola = starty 2015–2023.
- **Výstup:**
  - bezpečné riziko na celém období (propadlo ≤ 10 %);
  - r* vybrané na vývoji, ověřené v kontrole.

**Pravidla rozhodnutí:**
1. **Základ měřítka se od teď počítá s F33 se stopem**, protože tak ji runner obchoduje. Nové bezpečné riziko nahradí 1,0 %.
2. Když je F33 se stopem v kterémkoli období horší o víc než 0,05 R na obchod, zapíše se, že stop v runneru F33 oslabuje. **Jen informace, runner se nemění.**

Skript `scratch/f87_f33_stop.py`, výstup `research_data/prop/f87_souhrn.txt`.

## Výsledky (2026-11-25)
Výstup `research_data/prop/f87_souhrn.txt`.

**F33 se stopem:** zastaveno 5 ze 400 obchodů.
| Období | Bez stopu | Se stopem | Rozdíl |
|---|---|---|---|
| 2003–2018 | +0,102 R | +0,100 R | −0,002 |
| 2019–2026 | +0,077 R | +0,071 R | −0,006 |

Stop F33 skoro nic nebere. Únor 2020 na NAS ale otevřel gapem pod stopem, takže tam se stopem vyšlo −1,58 R místo −0,89 R.

**Měřítko F33 se stopem + RSI(2):**
| Riziko | Prošlo do 12 / 24 / 36 m | Propadlo | Medián |
|---|---|---|---|
| 1,0 % | 0 % / 8 % / 39 % | 0 % | 31,0 měs. |
| **1,25 % (nové bezpečné)** | **3 % / 17 % / 65 %** | **3 %** | **27,2 měs.** |
| 1,5 % | 7 % / 41 % / 75 % | 14 % | 23,7 měs. |

- r* vybrané na vývoji = 1,5 %, v kontrole ale propadlo 33 %.
- **Rozhodnutí:**
  1. Základ měřítka = F33 se stopem, **bezpečné riziko 1,25 %** (dřív 1,0 %).
  2. Stop F33 neoslabuje (rozdíl < 0,05 R).
- Zkouška tím zrychlí jen mírně: typicky z ~31 na ~27 měsíců. Runner se nemění.
