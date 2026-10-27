# Simulátor obchodování

Webová aplikace (Next.js) se simulovaným brokerem, živými daty, botem a agenty, kteří
rozhodují o každém obchodu. Žádné skutečné peníze.

## Ovládání
- **▶ AKTIVOVAT** (vpravo nahoře): bot začne sám obchodovat. V režimu *Bere co jde* vezme každý
  signál, který projde tvrdými kontrolami (Validátor, Trh teď, Risk); Statistik a Ďáblův
  advokát jen radí. Zelený pruh ukazuje dnešní počet signálů, vzatých a zamítnutých obchodů,
  graf skáče na trh nového obchodu. **■ ZASTAVIT** bota vypne (otevřené pozice dál běží).
- **Bot živě:** ruční BUY/SELL přes agenty (+ „Přesto vzít“, když jsou proti jen poradci)
  a přehled, na co která strategie právě čeká.
- *Opatrný* režim (Nastavení): nebere, když jsou proti aspoň dva poradci.

## Co v ní je
- **Graf** jako TradingView (knihovna `lightweight-charts`): svíčky 1m–1d, šipky vstupů,
  šedé × u zamítnutých signálů, čtverečky výstupů s výsledkem, čáry vstupu/SL/TP.
- **Data:** krypto živě z Binance (WebSocket přímo z prohlížeče), forex/indexy/kovy/ropa
  z Yahoo Finance přes `/api/candles` (prohlížeč na Yahoo napřímo nesmí).
- **Simulovaný broker** s podmínkami skutečného účtu z MT5 (`lib/broker.json`): spread po
  hodinách včetně přirážky, swapy (3× v den brokera), hodnota pohybu v USD, min. lot a krok.
  Limity prop firmy: denní ztráta 4 %, drawdown 8 %, cíl 8 % (z equity).
- **Strategie** převedené 1:1 z Python bota (`lib/strategies.ts`) + rychlá ukázka na 1m kryptu.
- **Místnost agentů:** Validátor, Trh teď, Statistik, Risk (stejní jako v `tv_agent/agents.py`)
  a Ďáblův advokát; Rozhodčí z hlasů rozhodne BERU / NEBERU.
- **Deník a stínové výsledky:** každý signál (i zamítnutý) se dopočítá, takže jde vidět,
  jestli agenti filtrují lépe než náhoda.

Bot běží v prohlížeči, dokud je stránka otevřená. Stav je v `localStorage`; po návratu se
otevřené pozice dopočítají ze svíček (SL/TP, swapy).

## Spuštění a nasazení
**Jen na tomhle PC:** dvojklik na `spustit-simulator.bat` → otevře se http://localhost:3000
(okno nech otevřené, zavřením se simulátor vypne).

Na Vercelu je veřejná jen adresa **https://trading-simulator-delta.vercel.app**. Adresy
s `matej02s-projects` v názvu (i ta z tlačítka „Visit“ ve Vercelu) chtějí přihlášení do Vercelu.

```
npm install
npm run dev                  # vývoj, http://localhost:3000
npx vercel deploy --prod     # nasazení na Vercel (zdarma, Hobby)
```

Lokální verze a verze na Vercelu mají každá svůj účet a deník (ukládá je prohlížeč pro danou adresu).

Podmínky brokera se obnoví z MT5 (ve složce bota): `python export_broker_conditions.py`.

## Kontroly
```
npx tsx scripts/test-sim.ts                      # broker: SL/TP, gap, swapy, velikost pozice
npx tsx scripts/compare-signals.ts <json>        # signály TS vs Python na stejných datech
npx tsx scripts/demo-frequency.ts                # jak často dává ukázka signál
```
