---
tags: [koncept, objem]
aktualizovano: 2026-10-29
---
# Futures data a objem (forex nemá centrální objem)
Zdroj: FM ([[FM Základy tradingu]], Hvězda, Šrajer, Kimmel) · Skupina: objem / data

## Definice
Forex je decentralizovaný. Objem v grafu je jen od jednoho brokera nebo **tickový** (počet změn ceny).
Skutečný objem mají futures na CME.

## Jak ho poznat (mechanicky)
- **Mapování:**
  - Forex: EURUSD → **6E**, GBPUSD → 6B, USDJPY → **6J (obráceně)**, AUDUSD → 6A, USDCAD → 6C (obráceně), USDCHF → 6S, NZDUSD → 6N, DXY → DX.
  - Komodity a indexy: zlato → **GC**, stříbro → SI, ropa → CL, S&P → **ES**/MES, Nasdaq → **NQ**/MNQ, Dow → YM.
- **Unadjusted graf** pro S/D a levely, protože adjusted posouvá ceny kvůli rolloveru.
  Rollover je zhruba týden před expirací (březen, červen, září, prosinec).
- FM mentoři **kreslí zóny na futures grafech a obchodují na CFD.** Dotek zóny na futures platí, i když na CFD cena vypadá jinak.

## Obchod
Volume profile, VWAP a sweepy „s velkým objemem“ mají smysl jen s reálným objemem.

## Souvisí s
[[Volume profile]] · [[VWAP]] · [[Zdroje dat]] · [[MT5 napojení]]

## Otestováno
V F5 a F7 jsme u forexu a zlata měli jen tick volume z MT5, u krypta reálný objem Binance. Volume koncepty nefungovaly ani na kryptu.
Zdarma futures M1 data nemáme (CME je placené, TradingView CME ~4 $/měs.), viz [[Zdroje dat]].
