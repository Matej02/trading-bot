---
tags: [vyzkum, souhrn, prinosy]
datum: 2026-11-19
---
# Souhrn přínosů výzkumu (2026-11-19)

Zadání uživatele (2026-11-19): „Dej info, co se nám může hodit celkově ode všech, které tam aktuálně nemáme přidané.“ Pravidlo uživatele: do bota jen to, u čeho jsme si „na 100 % jistí“ ([[Cesta k prop účtu]]).

## Co prošlo plnou prověrkou (pravidla předem, vývoj + kontrola + druhý zdroj + jiné trhy)
| Strategie | Kde je dnes | Síla |
|---|---|---|
| [[F33 Rebalancování na konci měsíce|F33]] | simulátor + MT5 demo | +0,23 R/měsíc od 2019, slábne ([[F40 F33 na dalších indexech|F40]]) |
| [[F42 RSI(2) přísná prověrka|F42 RSI(2)]] | jen simulátor | +0,09 R/obchod, převis nad driftem +0,06 R, odolná (9/9 variant) |

## Co nemáme a může se hodit
1. **RSI(2) na MT5 demu (US indexy).** Jediná nově ověřená strategie, která na demu chybí.
   - Malá, ale stálá výhoda, ~17 vstupů ročně. Profil opačný k F33 (časté malé výhry), dobře se doplňují.
   - Podle pravidla uživatele až po sledování dopředu v simulátoru a s výslovným souhlasem.
2. **Poznatky pro bezpečnost, bez nových obchodů:**
   - kalendářní efekty se v čase střídají (F31, F37, F38, F40), takže každou strategii je potřeba průběžně sledovat proti testu a vypnout, když se chová jinak;
   - u dat HistData čas = New York s letním časem a je potřeba filtrovat chybné ticky.

## Co v botovi je, ale přísnou prověrkou neprošlo (jen informace, bez pokynu se nemění)
- **Simulátor:**
  - [[Průraz F2 (proraz_d1)|Průraz F2]] (F43: nad driftem t 0,85 a 0,80);
  - [[Momentum L=250]] (bez čisté výhody, swapy TRY);
  - FM systémy (F9 zóny a další, neověřené).
- **MT5 demo:** F12–F16, F20 (dříve bez výhody), F31 (kandidát, jen od 2019), F29 (těsně neprošla).
- **Pro live by podle pravidla uživatele šly zatím jen F33 a RSI(2).**

## Co neprošlo dnes (2026-11-19)
- F35 fixing FX, F36 OPEX, F37 den před svátkem, F38 ECB, F39 momentum bez měn ([[Fronta nápadů F35–F39]]).
- F40 F33 v Evropě, F41 FOMC drift v Evropě 2010–18, F43 Průraz F2.
