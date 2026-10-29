# F10 – entry modely mentorů FM přesně podle PDF (minutová data)

Zadání uživatele (2026-10-29): otestovat i 3 dosud netestované strategie (Veselovský, Kimmel, Pátek) a všechno, co je v FM PDF.
Dokument z Wordu (F7) už se nepoužívá.
Pravidla jsou z vaultu `znalosti/FM/` (text i grafy). Volné parametry jsou jen tam, kde PDF dává víc možností. **Plán je sepsaný před spuštěním.**

## Data a náklady
- MT5 M1 (server Londýn → UTC, NY čas pro sessions):
  - forex EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD a kovy XAUUSD, XAGUSD od 2017;
  - NAS100mini, SPX500mini, US30mini, GER_30mini a CRUDE_OIL od 2019-02;
  - BTC a ETH (Binance) od 2022-09.
- Vyšší TF se skládají z M1. Den = 17:00–17:00 NY. Časy z PDF (CET) jsou převedené na NY (CET − 6 h).
- Simulace `f7_lib.sim_trade` na M1: spread brokera podle hodiny, swapy, limit se vyplní průchodem o 1 tick, SL a TP v jedné svíčce = SL.
- **Vývoj do 2021-12-31, OOS od 2022-01-01.** Krypto je celé OOS.

## Strategie (každá s ≤ 4 variantami z PDF)
1. **Veselovský (ICT, intraday):**
   - Bias D1 podle jeho pravidla. Killzone Londýn 02–05 NY nebo NY 08–11 NY.
   - Sweep Asie (20–02 NY) nebo PDL/PDH proti biasu, a to pod/nad NY open 00:00.
   - MSS na M5 (varianta M1): close nad high, ze kterého šel pohyb do sweepu, do 12 svíček, s FVG v noze.
   - Limit na 0,382 nohy (varianta: horní hrana první FVG). SL za extrém sweepu + 2 pipy.
   - TP1 = opačná strana Asie (50 %, pak BE), TP2 = PDH/PDL (alespoň 2R). Konec dne zavřít. Bez dnů FOMC, NFP a CPI.
2. **Kimmel (indexy, 09:30–12:00 NY):**
   - **M1 reverzní:** bias, dotek PDL/PDH na M15, MSS na M5, vstup trhem, SL o 25 % za extrém, TP 2R/3R.
   - **M2 pokračovací:** dotek M15 S/D zóny, 2 po sobě jdoucí BOS na M5 ve směru biasu, SL za zónu, TP 2R/3R.
   - Bias V nebo M.
3. **Pátek (NQ + GBPUSD, XAUUSD):**
   - Trend H4 podle struktury. Session 03–06 a 09:30–12 NY.
   - Na M5 vyšší low, pak close nad poslední pivot high (N=3) → long. SL pod poslední pivot low.
   - TP 2R / předchozí H4 high. Zrcadlově short.
4. **Šrajer day trading:**
   - M15 S/D zóna uvnitř aktivní 4H zóny stejného směru.
   - Před dotekem sweep M15 pivotu mezi cenou a zónou (likvidita).
   - Zóna v discountu/premiu 4H swingu.
   - Dotek v oknech 02:30–03:30, 04:30–05:30, 07:30–10:00 NY. Limit na proximal, SL za distal, TP 2,5R/3R, konec dne.
5. **Můčka:**
   - Asie 20–00 NY s range ≤ 35 pipů (EURUSD; jinde ≤ 0,47 ATR D1).
   - Sweep Asie v 03–05 nebo 07:30–11 NY, pak structure shift na M5.
   - Vstup trhem (varianta: limit golden pocket 0,618). SL na extrému sweepu, min 6 pipů.
   - TP opačná strana Asie / 2R. Varianta s filtrem barvy včerejší svíčky.
6. **Valchář (H4/D1):**
   - Trend D1. H4 OB = poslední opačná svíčka před impulzem s BOS; **POC impulzu (M1 tick volume) leží v OB**.
   - Před dotekem sweep H4 pivotu nad OB. Limit na hraně OB, SL za OB.
   - TP = high impulzu (RR 1,8–6, jinak se neobchoduje). Bez BE, nejdéle 30 dní.
7. **Hakimi (H4):**
   - Trend H4, poslední noha pivot → pivot.
   - Pullback do Fibo 0,5–0,75, kde se kryje S/D zóna H4 nebo FVG H4.
   - Limit 0,618, SL za zónou nebo low nohy, TP high nohy. RR ≥ 2,5, bez BE.
8. **Hvězda (D1):** D1 zóna, trend 2 HH a 2 HL, dotek a **potvrzovací svíčka hammer nebo engulfing** do 3 dní.
   Vstup trhem, SL za zónu (+20 %), TP 2R / protější zóna, BE při 1R. 26 trhů z H1 dat.

## Prahy
- OOS: n ≥ 100, exp ≥ 0,15 R, PF ≥ 1,3.
- O ≥ 0,1 R lepší než náhodné vstupy (stejný trh a rok, stejný čas dne, směr, SL v ATR D1, R cíle a výstup).
- Varianta se vybírá na vývoji. Kontrola zpožděného vstupu. Co projde → simulátor (live).

## Výsledky (2026-10-29) – detail ve vaultu `znalosti/Výzkum/F10 Entry modely mentorů FM.md`
- OOS 2022–26 s náklady: Veselovský −0,24, Kimmel −0,04, Pátek −0,05, Šrajer DT −0,29, Můčka −0,23, Valchář −0,36, Hakimi −0,44, Hvězda −0,21 R.
  Nic neprošlo.
- Bez nákladů jsou intradenní modely ~0 jako náhoda. Valchář a Hakimi −0,37 R (horší než náhoda i bez nákladů).
