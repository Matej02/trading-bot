# F7 – test 6 strategií z dokumentu „Trading bot – 6 strategií (SMC + Volume Profile)“

Zadání uživatele (2026-10-28): „tady máš všechny strategie, vše testuj a podle toho zjisti, co je nejlepší“.
Dokument: `scratch/docx/strategie.docx` (text v `scratch/docx/strategie.txt`).

## Úkoly
1. **Data** (`research_f7_data.py`):
   - MT5 terminál dá nejvýš 100 000 svíček, takže M1 jen ~3 měsíce, M5 ~1,5 roku a M15 ~4 roky. V historii je díra 10/2025–10/2026.
   - Krypto M1 z oficiálních veřejných dat Binance, 09/2022–10/2026: BTC/ETH/SOL podle dokumentu a navíc XRP, BNB, ADA, DOGE, LTC a LINK kvůli většímu vzorku.
   - Forex a komodity z MT5 na M15 a M5.
   - Dukascopy odmítlo automatické stahování (limit pro roboty), proto se nepoužilo.
   - Čas serveru brokera = Londýn (GMT/BST). Všechno se převádí na NY čas.
2. **Stavební bloky** (`f7_lib.py`): pivoty, struktura/BOS, displacement, MSS, FVG, RVOL podle času dne, volume profil (POC/VAH/VAL/HVN/LVN), VWAP ±σ, režim balance/trend, likvidita (PDH/PDL, PWH/PWL, Asie, Londýn, EQH/EQL) a S/D zóny H4.
3. **Simulace** (`f7_lib.sim_trade`):
   - Bid data; long platí ask (spread brokera podle hodiny).
   - Limit se vyplní až průchodem o 1 tick. SL a TP v jedné svíčce se počítá jako SL.
   - Parciální výstupy, BE, trailing, časové výstupy, swapy, skluz 1 tick.
4. **Strategie S1–S6** (`research_f7.py`):
   - Věrná verze „doc“.
   - Varianty z rozsahů parametrů dokumentu a ablace (vypnutí jednoho filtru, „jádro“).
   - Pro každou VTF (M1/M3/M5/M15) vstup CE nebo trhem.
5. **Vyhodnocení** (`research_f7_eval.py`):
   - Výběr varianty jen na vývoji (do 2025-02), OOS od 2025-03 jednou.
   - Prahy dokumentu: n ≥ 100, exp ≥ 0,15 R, PF ≥ 1,3, MC95 DD ≤ 15 R, ziskové kvartály ≥ 60 %, o 0,1 R lepší než náhoda, plato.
   - Walk-forward.
6. **Koncepty s velkým vzorkem** (`research_f7_koncepty.py`): SFP na každém druhu poolu, VWAP pullback v trendu, průraz z balance – trhem, TP 2R, proti náhodě.

## Průběh
- Kontrola trychtýře: přísné filtry se násobí. Například S1 na zlatě M15 za 4 roky: 407 SFP → 128 v killzone → 29 s RVOL ≥ 1,5 → 7 po filtrech → 0 s MSS.
- Opraveno: MSS se hledá už od extrému sweepu, ne až po zavření M15 svíčky se SFP. Na M1 se struktura láme uvnitř svíčky.
- Kontrola simulace: náhodné vstupy dávají −0,08 až −0,18 R, což odpovídá nákladům. Obchody S1 ručně zkontrolovány.
- Rozšířeno o 6 dalších kryptoměn (XRP, BNB, ADA, DOGE, LTC, LINK), jinak by vzorek nestačil.

## Výsledky (2026-10-28)
Výstupy: `research_data/f7/f7_vyhodnoceni.txt`, `f7_souhrn.csv`, `f7_koncepty.txt`, `f7_bez_nakladu.csv`,
`f7_kontrola_detekci_BTCUSD.png`, obchody `f7_obchody_*.pkl`.

1. **Věrná pravidla dokumentu skoro neobchodují.** Krypto (VTF M1–M15) dává 0,00–0,22 obchodu za rok na trh, forex a komodity (VTF M15) 0–0,42. Dokument odhaduje 1–5 obchodů týdně, tedy 50–250× víc. Nedosáhne se ani n ≥ 30, natož n ≥ 100 z dokumentu.
2. **Varianty z rozsahů dokumentu a ablace** („jádro“ = jen spouštěč a vstupní model) obchodují víc, ale jsou ztrátové a horší než náhoda:
   - S1-jádro krypto: vývoj −0,51 R (n 92), OOS −0,21 R (n 63).
   - S3 pravidlo 80 %: OOS −0,67 až −0,76 R.
   - S6-jádro: OOS −0,17 R.
   - Vybraná varianta S1 (jádro M1 CE): OOS −0,51 R, náhodné vstupy −0,29 R. Walk-forward −0,21 R.
   - Žádná strategie v žádné skupině neprošla. Většina nemá ani 30 obchodů na vývoji.
3. **Koncepty s velkým vzorkem** (vstup trhem, TP 2R):
   - Krypto: SFP na všech typech poolů −0,12 až −0,36 R na tisících sweepů. Pullback k VWAP −0,18 R (n 2 495, t −6,65).
   - Bez nákladů: SFP −0,027 R (n 11 895), VWAP −0,03 R. Výhoda tam není ani před spreadem (stejně jako F5 na 1h).
   - Forex a komodity: nic konzistentního. Zlato/komodity, pullback k VWAP: vývoj −0,02 R (n 256), OOS +0,10 R (n 68), tedy šum.
4. **Závěr:** žádná z 6 strategií ani jejich koncepty nemají doloženou výhodu. Do bota se nenasazují. Dál platí F2 průraz + RSI(2) z F6.
5. **Neotestováno:** forex a zlato s VTF M1–M5 na delší historii. Potřebuje nastavit v MT5 „Max. sloupců v grafu“ na neomezeně (dělá uživatel). Na kryptu, kde M1 bylo, to ale vyšlo jasně záporně.

## Doplnění 2026-10-29: forex a komodity na M1 (MT5 od 2020)
Uživatel nastavil v MT5 neomezený počet svíček → M1 od 2017; staženo od 2020 (`research_f7_data.py --mt5-m1`), skupiny `FOREX@M1`, `KOMODITY@M1`.
- Věrná pravidla i varianty: žádná varianta nemá ve vývoji n ≥ 30. S1-jádro forex −0,87 R (n 20), komodity −0,82 R (n 21); pravidlo 80 % −0,53 / −0,71 R.
- Koncepty: SFP forex −0,09 až −0,51 R, komodity −0,30 až +0,11 R (vývoj), nic konzistentního. VWAP pullback forex −0,16 R (n 450), komodity −0,03 R (n 458) – náznak u zlata zmizel.
- **Závěr F7 platí pro všechny třídy aktiv.** OOS forexu je krátký (díra v datech 10/2025–10/2026).
