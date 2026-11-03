---
tags: [koncept, smc]
aktualizovano: 2026-10-29
---
# Supply a demand zóny

Báze 1–4 malých svíček, odchod displacementem, cena se vzdálí ≥ 3× výšku báze. Skóre 0–4, obchodovat první dotek.
Zpřesnění přes HVN z [[Volume profile|profilu]] báze. [[F5 SMC a volume profile na 1h|F5]] (4h + HVN) −0,35 R;
[[F7 Dokument 6 strategií SMC|F7]] (S2) jen pár obchodů za 4 roky.

## Definice z dokumentu
- Báze 1–4 svíčky, každá rozsah ≤ 0,7 × ATR a tělo ≤ 50 % rozsahu; odchod = displacement, cena se vzdálí ≥ 3× výšku báze.
- Demand: proximal = nejvyšší tělo báze, distal = nejnižší low báze vč. knotu odchodové svíčky (supply zrcadlově).
- Čerstvost: jen 1. dotek (varianta 2.); zóna zaniká closem za distal.
- Skóre 0–4: odchod ≥ 2 ATR, báze ≤ 2 svíčky, odchod udělal BOS, odchod nechal FVG.
- Zpřesnění: fixed-range profil přes bázi a první impulz, HVN uvnitř zóny ± 1 bin (bez HVN POC báze); LVN v zóně = cena proletí.

## Jak je kreslí uživatel
_(doplní uživatel – podle něj dokument hledá zóny na špatných TF a moc malé: TF, velikost, pravidla, screenshot)_

Zdroj: [[Dokument 6 strategií SMC + Volume Profile|dokumentu 6 strategií]].

## Z materiálů FM (část 1, 2026-10-29) – jak kreslí S/D zóny mentoři
Podrobně v [[FM Základy tradingu]], [[FM Strategie – Daniel Hvězda (swing)]] a [[FM Strategie – Jan Šrajer (day + swing)]].
**Liší se od dokumentu 6 strategií hlavně timeframem a velikostí zóny.** To nejspíš odpovídá výtce uživatele („špatné TF, moc malé“).
- **Skladba:** pohyb dovnitř (několik středních nebo 2+ velké svíčky) + **konsolidace** (menší nerozhodné svíčky) + pohyb ven.
  **Zóna obsahuje celou konsolidaci**: na obrázcích má báze na D1 až 8–10 svíček, od extrému knotu po okraj těl.
  Kreslí se dvěma vodorovnými čarami, s širší a preferovanou (užší) verzí. Nástroj Parallel Channel má úrovně 0 / 0,75 / 1.
- **Platnost** (Šrajer, Hakimi, Můčka):
  - Po zóně **musí přijít impulzivní svíčka, která „něco dokázala“: prolomila high/low (BOS)**.
  - Zóna je **unmitigated**: mitigace max. **25 %** zóny.
  - Interní zóna drží 1–2 dotyky.
- **Pivotní vs interní:**
  - **Pivotní** = na otočení trendu (swing high/low), „o 30–50 % silnější“. Jen z nich se otevírají swingové obchody.
  - **Interní** = uvnitř trendu (pullback), slouží na správu pozice, BE a pyramidování.
  - RBR po velkém poklesu je slabá (přeprodanost).
- **Timeframy:**
  - Swing: zóny **W1 a D1 (M1)**, vstup na D1/H4. Hvězda: **D zóna uvnitř W zóny**.
  - Day trading: **4H zóny** (pivotní i interní) zpřesněné na **M15**. Šrajer: M15 zóna uvnitř 4H zóny.
  - Zónu, na kterou daný TF ještě neudělal impulzivní pohyb, hledat na nižším TF.
- **Lokace:** demand jen v discountu (spodní třetina mezi zónami), supply v premium → [[Premium a discount]].
  Trend na HTF: v uptrendu jen demand.
- **Vstup:** limit na proximal. **SL za distal** (Hvězda občas +20 % vzdálenosti; Můčka nikdy přímo nad zónu). TP nejbližší protizóna, ≥ 2R.
  BE při 1R (Hvězda), nebo bez BE (Valchář, Hakimi).
- **Konfluence:** POC/HVN z fixed range uvnitř zóny ji potvrzuje; **zóna v LVN je slabá**. Svíčka (hammer/engulfing) v zóně.
  Level nad levelem (dvě zóny těsně u sebe).
- **Data:** zóny se kreslí na **futures unadjusted** grafech → [[Futures data a objem]].

![[FM S-D zóny – RBR a DBR (Šrajer, D1).png]]
![[FM S-D zóny – skladba zóny (Hvězda).png]]

**Otázka pro uživatele:** kreslíš zóny takhle (celá konsolidace, D1/W1 nebo H4, impulz s BOS)? Případně doplň rozdíly v sekci výše.

## Doplněno uživatelem (2026-11-03)
Viz [[Doplňující pravidla k FM PDF]], A4 (1D/4H/15m, hranice přes těla, příchod+base+odchod, BOS + HVN/POC, neplatí po průrazu > 25 %).

## Otestováno – F8 (2026-10-29)
- **F12 (2026-11-03):** zóny jen s BOS, hranice přes těla, první dotek a pravidlo 25 %: zlepší OOS, ale ne vývoj, malé vzorky ([[F12 Můčka podle doplňujících pravidel]]).
Zóny kreslené podle FM (báze, impulz s BOS, první dotek, limit, SL za distal) na **D1, H4 a D v W**, 26 trhů, 2009–2026:
OOS −0,17 R (H4) a −0,22 R (D1), náhodné vstupy −0,04 až −0,07 R. Plato záporné, žádná z 192 variant neprošla.
Detail v [[F8 Strategie z FM PDF]]. Výhodu zóny nemají na žádném TF (F5 1h, F7 M1–M15, F8 H4–W1).

F9 (2026-10-29): jako spouštěč i filtr v 2 208 kombinacích ([[F9 Kombinace FM konceptů]]) – bez výhody.
