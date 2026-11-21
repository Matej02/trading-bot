---
tags: [vyzkum, plan]
datum: 2026-11-21
---
# F66 až F68: návrat k průměru (relativní, RSI(2) ve světě, noc po poklesu)

Zadání uživatele (2026-11-21): „A pak pokračuj, dokud nezjistíš zase nějakou výhodnou strategii.“ Plán je zapsaný **před výpočtem**, pravidla se po výsledku nemění.

**Proč tahle rodina:**
- Kalendářní a časové jevy od 2019 mizí ([[F65 Přelom měsíce na světových indexech|F65]], [[F63 a F64 Den před svátkem v Evropě a hodiny bitcoinu|F63]], F60, F59…).
- Jediné, co od 2019 vydrželo, je návrat k průměru na amerických indexech ([[F42 RSI(2) přísná prověrka|F42 RSI(2)]]). Ekonomický důvod: kdo dodá likviditu po výprodeji, dostane zaplaceno.
- Tři nové varianty, každá z jiného úhlu.

**Společné:**
- R = výsledek / ATR20, není-li uvedeno jinak.
- Náklady: spread a swap brokera, u trhů bez brokera 2 bp na vstupu i výstupu a swap −1 bp za noc (jako F65).
- Data Yahoo: řádky bez rozpětí pryč. Roky, kde se otevření rovná předchozímu zavření ve víc než 50 % dní, se u testů s otevřením vyřadí.

## F66 Relativní návrat mezi indexy
- **Trhy:** 8 indexů brokera (S&P 500, Nasdaq 100, Dow, DAX, FTSE, CAC, Euro Stoxx, IBEX). Yahoo denní 1990–2026, broker H1 → denní 2019–2026.
- **Každý týden:**
  - na zavření posledního obchodního dne týdne se spočítá z = (zavření − zavření o 5 obchodních dní dřív) / ATR20 každého trhu;
  - **long trh s nejnižším z**, drží se do zavření posledního obchodního dne příštího týdne;
  - pořadí se počítá, jen když má data aspoň 4 trhy.
- **Srovnání:** průměr stejného týdenního obchodu na všech trzích, které ten týden mají data. Převis = R vybraného − průměr R všech. t = průměr převisu / chyba (po týdnech).
- **ANO jen když platí vše:**
  1. Vývoj (Yahoo 1990–2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. Broker 2019–2026: signál > 0 a převis > 0.
  4. Převis kladný aspoň v 55 % let.
  5. Jiné trhy: stejné pravidlo na 10 světových indexech z F65, celé období, převis > 0.

## F67 RSI(2) na světových indexech (nezávislé ověření F42)
- **Pravidlo F42 beze změny:**
  - zavření nad SMA200 a RSI(2) < 10 → vstup na otevření dalšího dne;
  - ven na zavření nad SMA5, stop 3 ATR nebo po 10 dnech;
  - R = výsledek / 3 ATR.
- **Srovnání:** stejné vstupy a výstupy ve všech dnech nad SMA200 (drift).
- **Trhy:** 10 indexů z F65 (Nikkei, ASX, SMI, AEX, BEL 20, Hang Seng, TSX, KOSPI, TAIEX, STI). Žádný z nich se v F42 ani F49 nepoužil. Broker je nemá, jde čistě o ověření robustnosti RSI(2), které běží na demu.
- **ANO jen když platí vše:**
  1. Všech 10 dohromady, celé období: signál > 0, převis > 0, t ≥ 2,0.
  2. Všech 10 dohromady, 2019–2026: signál > 0 a převis > 0.
  3. Převis > 0 aspoň na 7 z 10 trhů.
  4. Převis kladný aspoň v 55 % let.

## F68 Noc po výrazném poklesu (US indexy)
- **Signál:** den, kdy zavření − předchozí zavření ≤ −1,0 × ATR20 (z předchozích dní).
- **Obchod:** long od zavření toho dne do otevření dalšího obchodního dne.
- **Broker (H1 ve skutečném UTC):**
  - vstup na zavření svíčky 15:00–16:00 NY;
  - výstup na otevření svíčky 09:00 NY dalšího obchodního dne;
  - pokles dne se počítá ze zavření 16:00 NY.
- **Srovnání:** stejná noc ve všech ostatních dnech. Převis, Welch t, po dnech (průměr SPX, NAS, US30).
- **ANO jen když platí vše:**
  1. Vývoj (Yahoo 1990–2018): signál > 0, převis > 0, t ≥ 2,0.
  2. Kontrola (Yahoo 2019–2026): signál > 0, převis > 0, t ≥ 1,5.
  3. Broker 2019–2026: signál > 0 a převis > 0.
  4. Převis kladný aspoň v 55 % let.
  5. Jiné trhy (DAX, FTSE, CAC, Yahoo celé období): převis > 0.
- **Popis navíc:** kolik signálů F68 padne na den vstupu RSI(2) na stejném trhu.

Skript `scratch/f66_f68.py`, výstup `research_data/f66/souhrn.txt`.

## Výsledky (2026-11-21): všechny tři BEZ VÝHODY
Souhrn: `research_data/f66/souhrn.txt`.

| Test | Vývoj do 2018 | Kontrola 2019–26 | Broker 2019+ | Jiné trhy | Roky | Verdikt |
|---|---|---|---|---|---|---|
| **F66** relativní návrat mezi indexy | převis +0,062, **t 2,67** | −0,047 (t −1,00) | −0,019 | +0,011 | 62 % | BEZ VÝHODY |
| **F67** RSI(2) na 10 světových indexech | celé období převis +0,017, t 1,32; signál −0,001 R | +0,015 | – | 6 z 10 trhů | 53 % | NEPOTVRZENO |
| **F68** noc po poklesu ≥ 1 ATR | převis +0,021, **t 2,01** | −0,025 | −0,030 | −0,013 | 53 % | BEZ VÝHODY |

- **F66 a F68:**
  - zase vzorec „do 2018 ano, od 2019 ne“;
  - u F68 je 27 % signálů ve stejný den jako RSI(2).
- **F67 je důležité zjištění pro RSI(2) na demu:**
  - mimo USA pravidlo nefunguje: světové indexy jsou kolem nuly a Evropa už v [[F49 RSI(2) na evropských indexech|F49]];
  - úspěšnost je všude 59–69 %, ale po nákladech a proti driftu nic;
  - **výhoda RSI(2) je americký jev**, ne obecná vlastnost akciových indexů;
  - pro demo to nic nemění: RSI(2) prošlo přísnou prověrkou na US indexech včetně kontroly 2019+ a brokera;
  - je to ale další důvod hodnotit ho podle sledování dopředu, ne podle historie.

Počet testů od F35: 36, prošly 2.

