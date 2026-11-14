---
tags: [od-uzivatele, simulator, export, tydenni-kontrola]
datum: 2026-11-14
---
# Export simulátoru 2026-11-14 (týdenní kontrola, předčasně v sobotu)

Soubory od uživatele (kopie v `scratch/exporty/2026-11-14`):
- `obchody-2026-11-14.csv`: 15 řádků uzavřených obchodů, z toho 4 duplicitní;
- `denik-2026-11-14.csv`: 135 rozhodnutí;
- `simulator-data-2026-11-14.json`: export z 14. 11. 10:51 Praha, log 9. 11. 12:18 až 14. 11. 01:00.

Předchozí: [[Export simulátoru 2026-11-09]]. Pravidla kontroly: [[Simulátor#Týdenní kontrola exportu (pravidla předem, 2026-11-11)]].

Uživatel poslal export už v sobotu, protože o víkendu nic neběží. V pátek měl PC vypnuté. Runner na MT5 demu běžel jen 12. 11. do 14:30 a 13. 11. v 8:13–9:15, s 0 otevřenými pozicemi.

## Stav účtu
- Zůstatek **100 290,84 $** (+290,84 $ od resetu 9. 11.).
- 29 otevřených pozic: 26 momentum, 2 průraz D1 (ETH, BTC short) a 1 další. Plovoucí zisk/ztráta v exportu není.
- Účet není zastavený, denní limit nebyl překročen.

## Chyba: zdvojený běh momenta 10. 11. (opraveno 14. 11., commit 13ca7b8)
- Denní rozhodnutí momenta (15:00 UTC) proběhlo **dvakrát**, v 16:00:37 a v 16:07:52 Praha.
- Obě zavřela stejné 4 pozice se stejným id: FRA_40mini, NZDJPY, XAUUSD, GAUUSD.
- **Zůstatek je správně.** Započítal se jen druhý běh, zůstatek = součet bez prvního běhu.
- **Historie a log jsou špatně.** V `closed` a v CSV jsou 4 fantomové obchody za −230,71 $.
- Statistiky ze seznamu uzavřených obchodů jsou tedy zkreslené. Součet `closed` dává +60,13 $ místo +290,84 $.
- Pravděpodobná příčina: stav z prvního běhu se ztratil (účet a pozice se přepsaly, zatímco log a `closed` se jen připisují) a druhý běh rozhodl znovu. 10. 11. byl den častých nasazení. 11.–13. 11. se to neopakovalo.
- **Mechanismus podle kódu (nejpravděpodobnější, sedí na log i zůstatek):** karta prohlížeče v pozadí ztratila řízení (lease 2 min vypršel), server (cron) odbavil denní momentum a karta po probuzení se starým stavem udělala totéž znovu. Uložení zastaralého stavu server nekontroloval.
- **Oprava (uživatel schválil 14. 11. „A udělej“):**
  - Stav má číslo verze (`sim:rev`). Každé uložení posílá `baseRev`. Když se liší od verze na serveru, server uložení odmítne (`stale`) a zařízení načte celý stav znovu jako sledující.
  - Převzetí a reset verzi nekontrolují.
  - Načtení i export berou u stejného id pozice jen poslední záznam (ten je v zůstatku).
  - Test se souborovou databází: 11/11 OK. `tsc` a `next build` čisté.
  - Nasazeno 14. 11. 11:08 a první běh cronu v 11:10 na nové verzi bez chyby.
- **Dopad:** stará otevřená karta (starý kód bez verze) už nic neuloží, stačí ji obnovit (F5).

## Chování podle pravidel (jen zapsat, neměnit)
- **Vzaté obchody:**
  - momentum 7 obchodů, −0,46 R;
  - F9 zóna H4 NZDJPY short TP +2,96 R (+654,84 $ po swapu);
  - F14 NAS100 long SL −1 R;
  - ukázka BB 1m +0,17 R.
- **Momentum se točí kolem nuly:**
  - NZDUSD změnil směr 3 dny po sobě (short 10. 11., long 11. 11., zavřeno 12. 11.);
  - XAU, GAU a NZDJPY se otočily při výnosu za 250 dní jen −0,2 %.
  - Pravidlo nemá pásmo necitlivosti. Je to vlastnost pravidla, ne chyba.
- **Swapy u TRY:** otevřené USDTRY long (−214 $) a EURTRY long (−113 $) za 4–5 dní, dohromady asi −70 $/den. Je to největší nákladová položka. **Otázka pro výzkum:** počítal test momenta se swapy u TRY?
- **Risk zamítl 93 ze 135 signálů:**
  - 39× expozice na USD;
  - 26× lot pod minimem brokera (známý problém malé velikosti, [[Cesta k prop účtu]]);
  - 10× EUR, 6× GBP a další.
- **Stínové výsledky nevzatých signálů** (malé vzorky, nic z nich nevyvozovat):
  - BB squeeze H1 +3,73 R z 9;
  - pullback +1,88 R z 1;
  - 109 stínů je ještě otevřených.

## Další
- Pondělí 16. 11.: rozhodnutí F29 podle plánu.
- Runner 14. 11. visel na „Čekám 60 s na síť a MT5 po přihlášení“. Okno bylo v režimu výběru („Vybrat“ v titulku), což program pozastaví. Odblokuje se klávesou Esc v okně.
- Úloha [[Pohled na grafy (automaticky)]] od 12. 11. při každém běhu stojí na schválení nástrojů. Zatím nevznikla žádná poznámka kromě 11. 11.
