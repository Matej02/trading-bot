---
tags: [vyzkum, f11, fm]
datum: 2026-10-29
---
# F11 – mentoři FM znovu, po jednom a podrobně

Uživatel nesouhlasil s výsledky F10 („strategie lidem reálně vydělávají“) a chtěl každou strategii otestovat pomalu, zvlášť a s propojením všech prvků.
Kód je v `research_f11_*.py`, výstupy v `research_data/f11/`.

## 1. Kontrola testovacího motoru
[[Průraz F2 (proraz_d1)]] na stejných M1 datech a stejnou simulací (`X.sim`) dává **OOS 2022–26 +0,24 R** (zlato, NQ a ES +0,32 až +0,35 R, forex záporně).
To odpovídá původnímu F2. **Motor umí ukázat zisk, když výhoda existuje**, takže záporné výsledky mentorů nejsou chyba simulace.

## 2. Chyby nalezené v F10 (opraveno)
- **Hakimi:** SL mohl vyjít těsně pod vstupem (RR až 500:1). Teď je SL pod celou zónou, nejméně pod Fibo 0,75, a RR 2,5–8.
- **Náhodné vstupy u swingových strategií** dostávaly skutečnou dobu držení obchodu, která závisí na výsledku. Teď se používá pevné maximum.
  Valchář je i po opravě pod náhodou (−0,36 R proti −0,09 R).
- **Veselovský:** sweep bral i lokální M15 swingy a úroveň MSS byla maximum poslední hodiny. Podle jeho ukázky je to
  **první vybrání Asia low/high nebo PDL/PDH pod/nad NY open** a MSS = close za **posledním swingem před sweepem**. Přidán vstup do OB 50 % (z ukázky).
  ![[F11 Veselovský – ukázky obchodů z testu (EURUSD 2022).png]]

## 3. Výsledky v2 (vybraná varianta na vývoji, OOS 2022–26)
| Mentor | Co přibylo | OOS | Náhoda |
|---|---|---|---|
| [[FM Strategie – Michal Veselovský (day, ICT)\|Veselovský]] | první sweep Asie/PD, MSS od swingu, OB/FVG/0,382/GP, M5/M1, max 2 SL | −0,47 R (n 226) | −0,20 R |
| [[FM Strategie – Sunita Hakimi (day, zlato)\|Hakimi]] | SL pod zónou/0,75, H4+M15 zóny + FVG, limit / M15 potvrzení | limit −0,36 R; **M15 potvrzení −0,08 R** (n 781) | −0,06 R |
| [[FM Strategie – Rafael Kimmel (day, indexy ICT)\|Kimmel]] | 15m PDA z předchozího dne, best pair NQ/ES, FVG vstup, TP nad range | +0,08 R (n 196) | +0,08 R |
| [[FM Strategie – Oliver Pátek (scalping NQ)\|Pátek]] | odmítnutí na H4 úrovni, LH/HL, TP další pivot | −0,05 R (n 1 464), všech 6 variant −0,03 až −0,10 | −0,05 R |
| [[FM Strategie – Daniel Hvězda (swing)\|Hvězda]] | rozpad long na zlatě a indexech | malé n (14–35), náhodné longy +0,14 R | – |

## 4. Co se ukázalo napříč
- **Limit do zóny je ztrátový** (Veselovský, Hakimi, Valchář: −0,36 až −0,47 R). Když cena limit dotkne, častěji zónou projede, než se odrazí.
- **Vstup po potvrzení** (M15 svíčka zpět za úroveň, MSS trhem) dává zhruba náhodný výsledek (−0,1 až +0,08 R).
- Na indexech kopírují výsledky drift trhu (náhodné longy jsou stejně dobré).

## 5. Proč lidem s FM přesto chodí výplaty
Simulace prop challenge (1 % riziko, RR 1:2, 2 obchody denně):
- Trader **bez jakékoli výhody** projde **one-step (cíl 9 %, DD 6 %) v 38 %** a two-step (8 % + 5 %) v 34 %.
- I s mírně ztrátovou strategií (−0,05 R na obchod) projde 23–29 %.
- FM samo uvádí (Launchpad), že funded účet získá ~40 % jejich studentů a z 10 % funded lidí jen 2 získají payout. To odpovídá nulové výhodě.

Výplaty tedy existují, ale z výsledků vidíme jen ty, kterým to vyšlo. Ostatní kupují další challenge. Nedokazuje to, že pravidla mají výhodu.

## Závěr
Ani po opravách a podrobném převodu nemá žádná ze strategií mentorů doloženou výhodu. Do simulátoru se nic nového nepřidává.
Co funguje, je dál [[Průraz F2 (proraz_d1)]] a [[RSI(2) pullback (mr_rsi2_d1)]].
Nejbližší ke kladu: Hakimi s M15 potvrzením na zlatě a EURUSD (+0,06 až +0,08 R, neprůkazné) a Kimmel best pair na US30 (+0,33 R, n 62).
