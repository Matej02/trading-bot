---
tags: [projekt, prop, doporuceni]
datum: 2026-11-11
---
# Prop firmy – doporučení (2026-11-11)

Na otázku uživatele: „Jaké bys doporučil prop firmy? Jen si je zapiš do vaultu. Jde nám hlavně o to, aby to pro nás bylo co nejlepší a přizpůsobené nám.“ Navazuje na [[Cesta k prop účtu]] (krok 3).

> Rozbor pravidel podle veřejných stránek k 11. 11. 2026, ne finanční doporučení. Pravidla firmy často mění. **Před nákupem je ověřit znovu na oficiálním webu.** Nic se zatím nekupuje a bot se nemění.

## Co potřebujeme my (podle našich strategií)
- **MT5 a povolené vlastní EA.** Runner obchoduje automaticky přes MT5.
- **Držení přes noc a víkend.** [[F33 Rebalancování na konci měsíce|F33]] drží 2–4 dny na konci měsíce, takže občas přes víkend. [[F31 Drift před FOMC|F31]] drží přes noc.
- **Zprávy.** F31 zavírá ve 13:55 NY, 5 minut před FOMC. Vadí tedy jen přísná okna kolem zpráv delší než 5 minut.
- **Neaktivita.** F33 a F31 obchodují jen asi 8× ročně. **Pravidlo „30 dní bez obchodu = konec účtu“ je pro nás největší past.** Řešení: běží i další strategie (častější obchody), nebo zmrazení účtu, pokud ho firma nabízí.
- **Bez časového limitu zkoušky.** Málo obchodů znamená pomalý postup.
- **Velký účet stačí na minimální loty indexových CFD.** Na 100k $ F33 velikostí vyjde.
- **Statický maximální propad** je pro nás lepší než klouzavý.

## Doporučené pořadí

### 1. FTMO – účet Swing, 2 kroky (první volba)
- **Proč nám sedí:**
  - Česká firma z Prahy: česká podpora a nejdelší historie výplat.
  - Vlastní EA výslovně povolené (pozor jen na „hyperaktivitu“ serveru, my obchodujeme málo).
  - MT5.
  - Ve zkoušce lze držet přes víkend.
  - Na financovaném účtu to dovoluje jen typ **Swing**, standardní účet musí zavírat před víkendem a má omezení kolem zpráv. **Proto jen Swing.**
- **Rizika pro nás:**
  - Neaktivita: FAQ uvádí, že při 30 dnech bez obchodu ve zkoušce může být ukončena. Ověřit, jestli jde účet zmrazit.
  - Cizí EA nevadí, náš runner je vlastní.
- **Ověřit před nákupem:**
  - aktuální cenu;
  - denní limit (z equity / zůstatku, čas resetu);
  - podíl na zisku;
  - specifikaci US500/US100 a XAUUSD (lot, $/bod, swap);
  - časový limit zkoušky.
- Zdroje: [FTMO – držení přes noc a víkend](https://ftmo.com/en/faq/can-i-hold-positions-overnight-or-over-the-weekend/), [FTMO – povolené strategie](https://ftmo.com/en/faq/which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/), [FTMO FAQ neaktivita (ftmo.oanda.com)](https://ftmo.oanda.com/faq/how-long-does-it-take-to-become-an-ftmo-verified-prop-trader/).

### 2. The5ers – High Stakes, 2 kroky (záloha)
- **Proč:**
  - EA povolené, zakázané jsou jen nekalé (kopírování, zneužití rolloveru, spam serveru).
  - MT5.
  - Držení přes víkend povolené, u indexů ale vysoký swap.
- **Rizika:**
  - Neaktivita 30 dní ve zkoušce, počítá se od registrace. Na financovaném (Pro) účtu 60 dní.
  - Zákaz otevírat a zavírat obchody 2 min před a po důležité zprávě. Zisk z té doby se odebere. Výstup F31 ve 13:55 je mimo okno, ale runner by to musel hlídat.
- Zdroje: [The5ers – pravidla High Stakes](https://the5ers.com/faqs/what-are-the-general-rules-for-the-high-stakes-program/), [The5ers – zakázané praktiky](https://the5ers.com/faqs/prohibited-trading-practices/).

### 3. Fintokei (zvážit až po ověření)
- **Plus:**
  - Česká firma.
  - Vlastní EA povolené (komerční a veřejné boty ne).
  - Držení přes noc a víkend povolené.
- **Mínus:**
  - Zkouška má podle přehledu limit 60 obchodních dní. To je pro málo obchodů špatné.
  - Neaktivita 30 dní.
  - Uváděné limity propadu se mezi zdroji liší. Ověřit na oficiálních stránkách.
- Zdroj (třetí strana, kontrola 29. 7. 2026): [Propvator – Fintokei](https://propvator.com/fintokei/rules/).

### Nedoporučuji
- **FundedNext:** pravidlo držení přes víkend v roce 2026 vypnuli (leden) a zase zapnuli (květen). Pro strategii, která na tom stojí, je to nestabilní. Zdroj: [TheGodFunded – zpráva](https://thegodfunded.com/en/news/fundednext-reinstates-weekend-holding-for-trading-accounts).
- **Futures prop firmy** (Topstep, Apex apod.): nejedou na MT5 a často vyžadují zavřít pozice do konce dne. F33 ani F31 tam nejdou.
- **Firmy s denním limitem 2–3 % nebo maximálním propadem 3–6 %, „instant funding“ a nové firmy bez historie výplat:** naše strategie mají ztrátové série a hrozí rychlé propadnutí.

## Přizpůsobení nám (až na pokyn uživatele)
- **Riziko:** na prop účtu se drží pod limity firmy. Vlastní pojistka −3 % za den a −8 % celkem, SPX a NAS jako jedno riziko, viz [[F34 Limit rizika pro korelované trhy]].
- **Neaktivita:** v runneru hlídat dny od posledního obchodu a upozornit uživatele (ne vynucovat obchod). Řešit spíš víc strategiemi.
- **Velikost účtu:** spíš 100k $ než 10–25k $, aby F33 vyšla na minimální lot. Cenu porovnat s výpočtem očekávané hodnoty (krok 6 v [[Cesta k prop účtu]]).
- **Typ:** 2kroková zkouška se statickým propadem. 1kroková mívá klouzavý propad a přísnější denní limit.

## Stav
- Doporučení je jen pro budoucí rozhodnutí. Rozhodující je pořád krok 1 (víc ověřených strategií).
- Uživatel může vybrat i jiné firmy. Claude je porovná podle stejných bodů.
