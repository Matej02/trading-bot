---
tags: [fm, zdroj, strategie, daytrading, ict]
zdroj: "D:\\youtube\\FM pdfka\\Strategie\\Michal Veselovský - Day Trading Strategie (PDF)"
zpracovano: 2026-10-29
---
# FM – Michal Veselovský: Day Trading (daily bias + PO3/AMD + MSS, ICT)

32 PDF, 146 stran. Hlavně EURUSD (jde i na jiný forex a zlato), Londýnská seance, SL 5–10 pipů. Má funded účty od 4/2024.
Je to nejmechaničtější day-trading strategie v materiálech. Viz [[FM materiály]].

## Daily bias (pravidla) → [[Daily bias]]
Na D1 se z poslední denní svíčky určí směr dne. Obchoduje se jen ve směru biasu, a po dosažení targetu i proti němu.
- **Close těla nad PDH** → dnes se čeká pohyb nahoru (pokračování k dalšímu high).
- **Jen sweep PDH a close pod ním** → dnes bearish, cíl PDL. Zrcadlově pro PDL.
- **Close uvnitř knotu:** nad 50 % knotu bullish, pod 50 % bearish.
- **Range:** neobchodovat, dokud se viditelně neuzavře mimo range.
- K tomu D1 FVG a OB, stará denní maxima a minima (zbývá-li likvidita) a vztah close k včerejšímu targetu.
- Udává **70–80 % úspěšnost určení směru**. **To se dá přímo otestovat na D1 datech.**

## PO3 / AMD → [[Daily Open a Power of 3]]
1. **Akumulace:** asijská seance (02–08 CET), úzký range, tvoří likviditu.
2. **Manipulace:** sweep likvidity (Asia H/L, PDH/PDL, lokální H/L), falešný průraz.
   **Pro long musí proběhnout pod NY daily open, pro short nad ním.**
   NY daily open = open svíčky v 6:00 CET (NY půlnoc) na H1. Je tu i NY weekly open = pondělí 6:00.
3. **Distribuce:** hlavní pohyb dne ve směru biasu k opačné likviditě.

## Entry model → [[MSS a displacement]]
1. Bias je určený. Na H1/M15 jsou vyznačené zóny: **OB, FVG, iFVG, BPR**, Asia H/L, PDH/PDL, swing H/L, NY DO/WO a VWAP.
2. **Bez výběru likvidity se nevstupuje.**
3. Po sweepu přijde **MSS na M1/M5 s displacementem (momentem)**: trh prorazí low/high, které tvořilo BOS.
   **MSS musí vzniknout v důležité zóně, jinde je bezcenný.** MSS knotem nestačí.
4. Vstup **limitem** na pullback do zóny po MSS: **první FVG s 0,382**, golden pocket (0,618–0,66, u EURUSD i 0,705–0,75), iFVG nebo OB.
   U OB z více svíček lze vstoupit na 50 % jejich těl.
5. **SL** ±2 pipy za swing (rezerva na sweep).
6. **TP1** na opačné straně asijského range a pak SL na BE. **TP2** = daily bias target (PDH/PDL).
   Předčasný výstup, když cena nemá sílu prorazit level a objeví se opačný signál.

## Pravidla dne
- **Killzones (CET):** Londýn **8–11** (long i v 11:30, „přes oběd to podle statistik jde nahoru“), NY **14–17**.
  Bez zpráv začíná NY už ve 13:00; při red news ve 14:30 od 14:00. Asie 2–8 je jen akumulace.
- **Max. 2 SL denně, každý 0,5 %**, protože jsou 2 zóny: horší a lepší.
- **Neobchoduje** FOMC, NFP, PPI, CPI a PMI. Ostatní red news obchoduje („doručí cenu tam, kam velcí chtějí“).
  Otevřený obchod přes zprávy drží, těsně před nimi nový neotevírá.
- **Reakce opačná než zpráva** (bearish data, cena roste) = manipulace, počkat na entry ve směru fundamentu.

## Definice → [[FVG]], [[Order block]], [[Likvidita]]
- **FVG:** mezera mezi svíčkami 1 a 3 kolem impulzivní svíčky 2. **Close za FVG ho ruší.**
- **iFVG:** FVG, kterým cena proletí a uzavře za ním. Otočí směr a slouží jako zóna v novém směru.
- **BPR:** býčí a medvědí FVG se překrývají; BPR je část, do které nezasahují knoty.
- **OB:**
  - Poslední opačná svíčka před prudkým pohybem. Jedna svíčka se bere celá i s knotem, skupina svíček jen těly.
  - **OB musí vzniknout na důležité úrovni** (po sweepu, ve FVG). Vstup se potvrzuje MSS na M1/M5.
- **ERL vs IRL:**
  - Externí likvidita (ERL) = swing H/L, PDH/PDL, lokální H/L, Asie.
  - Interní likvidita (IRL) = FVG, BPR, iFVG.
  - **Trh chodí z IRL do ERL a zpět.** Po vybrání starého high jde vyplnit imbalanci, kterou cestou vytvořil.
- **Balanční level** (H1 high/low proražené momentem a několikrát otestované) slouží jen jako konfluence.
- **Horizontals:** DO, NY DO (6:00), WO, MO.
  - Značí se **od těla**: u býčí svíčky spodek těla, u medvědí vršek.
  - Cena nad DO/WO je bullish. Průraz NY DO momentem na H1 bývá následovaný retestem.
- **RSI 14:** jen konfluence (70/30, divergence, přechod přes MA).

## Testovatelnost
**Velmi dobrá.** Daily bias je čistě mechanický a dá se ověřit na D1 s tisíci dny:
otázka je, zda podle pravidla trh dosáhne cíle častěji než naivně.
Celý model (Asie → sweep pod NY DO → MSS M1/M5 → FVG 0,382 → TP1 Asie, TP2 PDH/PDL) jde postavit nad M1 daty z MT5.
Dílčí prvky už byly negativní v [[F5 SMC a volume profile na 1h]] a [[F7 Dokument 6 strategií SMC]] (PO3, SFP, MSS).
Nový je **daily bias filtr** a **vstup pod/nad NY DO**.

## Z grafů v PDF (prohlédnuto všech obrázků, 2026-10-29)
- **Daily bias na D1 v praxi** (číslované kroky na denním grafu):
  1. Cena dojde pro low (externí LQ).
  2. Cestou vznikne imbalance (FVG, interní LQ) a čeká se její vyplnění.
  3. Trh ji vyplní a respektuje (close pod ní).
  4. Svíčka sweepne předchozí high a uzavře stažená pod imbalancí, takže se čeká pokles.
  5. Cena míří od interní LQ k externí (swing low).
  6. Svíčka uzavře nad 50 % předchozího knotu = bullish.

  **Je to celé na denních svíčkách, tedy přímo testovatelné.**
- **Management pozice (modelový obchod):**
  - Sweep asijského low, pak „vytvořený OB+, prolomení = níž“ a entry model.
  - **TP1 = opačná strana Asie a nastavení BE, TP2 = daily bias target** (high předchozího dne).
- **OB praxe:** OB je na HTF šedý box po sweepu, vstup na **0,5 OB**, TP jako velký modrý box (RR ~4+). Bullish OB leží na „important level“.
- **MSS:** BOS nahoře, pak MSS (průraz low, které tvořilo BOS) s momentem. Šikmá likvidita „LQ“ se vybere a teprve pak short.
- **AMD diagram:** akumulace (Asie) → manipulace pod úroveň akumulace → distribuce nahoru.
- **Killzones** (indikátor v UTC−4): Asia 20–02, Frankfurt 02–03, London 03–08 (killzone 03:30–06:30), NY 08–16 (killzone 08:30–10:30).
  V CET: Londýn 8–11, NY 14–17, Asie 2–8.
- **Horizontals:** NY dOpen a NY wOpen (kroužky). Reakce na NY DO na H1. „Efektivita NY DO a NY WO na 4h timeframu.“
- **SVP:** VAH/VAL 70 %, POC+HVN, LVN. Pád z VAL rovnou do další LVN.
