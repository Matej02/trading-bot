---
tags: [od-uzivatele, export]
aktualizovano: 2026-11-03
---
# Export simulátoru za týden (2026-10-27 až 2026-11-03)

`D:\Trading bot\scratch\exporty\simulator-data-2026-11-03.json`, rozbor ve skriptu `scratch/export_1103.py`.
Režim „bere co jde“ ([[Učící režim]]), riziko 0,25 % na obchod, denní limit 2 %, všech 10 systémů zapnutých.

| | |
|---|---|
| Účet | **39 851 $** (−60,1 % od startu 100 000 $; 2026-10-29 byl 89 331 $) |
| Uzavřeno | 329 obchodů, **−60 061 $** |
| `ukazka_ema_m1` | 180 obchodů, **−32 121 $**, win 24 % |
| `ukazka_m1` | 141 obchodů, **−27 367 $**, win 26 % |
| [[Momentum L=250]] | 6 uzavřených, −175 $; 27 pozic otevřených (swap zatím −399 $ na všech otevřených) |
| BB squeeze H1 | 2 obchody, −398 $ |
| FM experiment ([[F9 Kombinace FM konceptů]]) | 12 signálů, vzatý 1 (USDCHF short `fm_pruraz_h4`, stále otevřený) |
| [[Průraz F2 (proraz_d1)\|Průraz F2]], [[RSI(2) pullback (mr_rsi2_d1)\|RSI(2)]] | 2 a 5 signálů, nevzaté (veto) |

Nejhorší den byl 2026-11-01 (−17 460 $), vždy jen 1m ukázky.

## Proč 1m ukázky ztratily tolik (chyba simulace, ne jen strategie)
- Ukázky dávají na BTC stop jen **3–7 $ od vstupu** (0,01 % ceny), tedy **uvnitř spreadu**.
- Velikost pozice se počítá z této vzdálenosti, takže vychází obří loty (až strop 25 lotů).
- Obchod se zavře ve stejné sekundě, kdy se otevřel, protože druhá strana spreadu je už za SL. Skutečná ztráta je **−10 až −18 R** místo −1 R.
  - Příklad: 2026-11-01 01:30 BTC short 25 lotů, SL 6,71 $ od vstupu, výstup o 87 $ dál, −2 177 $.
- Ze 321 obchodů ukázek skončilo **108 hůř než −1,5 R**. Průměr −1,16 R.
- Obě ukázky braly často **stejný obchod ve stejnou chvíli** (dvojité riziko).
- Denní limit 2 % je počítaný z plánovaného rizika (0,25 %), takže ho jeden takový obchod přeskočí. Proto den −17 %.
- Reálný broker by stop uvnitř spreadu odmítl (stop level). Simulátor by měl takový signál vetovat (Risk: SL ≥ několikanásobek spreadu)
  nebo počítat velikost i se spreadem, viz [[Náklady brokera]].

## Ostatní
- **[[AI analytik]]** hlasoval skoro vždy NE (334× NE u 1m ukázek). Stínové obchody zamítnutých ukázek: −1,32 R a −0,86 R, vzatých −1,06 R a −1,21 R.
  Filtr tedy nepomohl, špatná je strategie.
- **FM experiment:** 11 z 12 signálů zablokoval Risk, hlavně kvůli **expozici na měnu** (JPY, USD), kterou zaplnilo 27 pozic Momentum.
  Za týden tak FM systémy nesbírají skoro žádná živá data. Stíny zamítnutých FM signálů: 3× −1 R (malý vzorek).
- Momentum: 10× veto pro expozici EUR, 10× GBP, 6× JPY; několikrát lot pod minimem brokera (indexy s min. 1 lotem).

## Závěr
- Stejný závěr jako [[Export simulátoru 2026-10-29]]: 1m ukázky jen pálí účet. Navíc má simulace u nich chybu se stopem uvnitř spreadu.
- Doporučení:
  - vypnout `ukazka_m1` a `ukazka_ema_m1` (vypíná uživatel v Nastavení);
  - opravit Risk (veto, když je SL blíž než ~3× spread);
  - u FM systémů zvážit, aby jim Momentum nebralo měnovou expozici.

Další export: [[Export simulátoru 2026-11-05]] (po vetu SL ≥ 3× spread už jen 2 ukázkové obchody za noc).
