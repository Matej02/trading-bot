# Simulátor obchodování

Webová aplikace (Next.js) se simulovaným brokerem, živými daty, botem a agenty, kteří
rozhodují o každém obchodu. Žádné skutečné peníze.

**Běží na:** https://trading-bot123-fawn.vercel.app (Vercel tým Weby_Korda, nasazuje se samo
z GitHubu https://github.com/Matej02/trading-bot, kořen projektu `simulator`).

## Ovládání
- **Přihlášení** heslem z `APP_PASSWORD` – na PC i mobilu stejný účet a celý deník.
- **▶ AKTIVOVAT** (vpravo nahoře): bot začne sám obchodovat. V režimu *Bere co jde* vezme každý
  signál, který projde tvrdými kontrolami (Validátor, Trh teď, Kalendář, Risk); Statistik,
  Ďáblův advokát a AI analytik jen radí. **■ ZASTAVIT** bota vypne (otevřené pozice dál běží).
- **Obchodovat jen ověřené** (Nastavení): Statistik vetuje vše neověřené – živě jde jen průraz z F2.
- **Bot živě:** ruční BUY/SELL přes agenty a přehled, na co která strategie právě čeká.
- **Deník:** stažení celé historie – Deník (CSV), Obchody (CSV), Vše pro rozbor (JSON).

## Bot nonstop (24/7)
Bota řídí vždy jen jedno místo: otevřená stránka má přednost, po jejím zavření ho do 5 minut
převezme server. Server budí bezplatná služba cron-job.org:
1. Vercel → projekt → Settings → Environment Variables: `TICK_SECRET` = dlouhý náhodný řetězec → Redeploy.
2. cron-job.org (zdarma) → Create cronjob → URL `https://trading-bot123-fawn.vercel.app/api/tick?key=<TICK_SECRET>`
   → každých 5 minut → uložit.
V hlavičce stránky pak svítí „server 24/7 před X min“.

## Agenti
| Agent | Co hlídá | Váha |
|---|---|---|
| Validátor | čerstvost signálu, utečená cena, duplicita | veto |
| Trh teď | víkend, pátek večer, rollover, spread | veto |
| Kalendář | zprávy s vysokým dopadem (ForexFactory, zdarma) – 30 min před a 15 min po; ukáže poslední vyhlášené číslo proti prognóze (FXStreet) | veto |
| Risk | denní limit (2 %), drawdown 8 %, velikost, expozice na měnu | veto |
| Statistik | jen setupy ověřené v registru (`lib/registry.json`) | radí / veto (Nastavení) |
| Ďáblův advokát | důvody proti (honění pohybu, proti trendu, série proher, swap) | radí |
| AI analytik | Gemini posoudí signál s kontextem: trend, RSI, spread vůči SL, příští zprávy, vyhlášená čísla za 24 h (lepší/horší než prognóza) a titulky zpráv k trhu (Google News + Yahoo Finance, `lib/server/news.ts`) | radí; veto až si ho vyslouží (níže) |

**Vysloužené veto AI** (`lib/aiScore.ts`): u každého signálu se zapisuje hlas AI a jak by signál dopadl.
NE od AI se stane tvrdým vetem, až je aspoň 30 vyhodnocených ANO i 30 NE, signály s NE vychází v průměru
ztrátově a ANO jsou lepší než NE s t ≥ 2. Když to přestane platit, veto zase zmizí. Skóre je v Deníku,
vypínač v Nastavení.

## Co v ní dál je
- **Graf** jako TradingView (`lightweight-charts`), svíčky 1m–1d, vstupy, výstupy, SL/TP, náš čas.
- **Data:** krypto z Binance, forex/indexy/kovy/ropa z Yahoo (`lib/yahoo.ts`).
- **Simulovaný broker** s podmínkami MT5 účtu (`lib/broker.json`): spread po hodinách, swapy, loty.
- **Strategie** převedené 1:1 z Pythonu (`lib/strategies.ts`), ověřený `proraz_d1` z F2.
- **Data na serveru:** Upstash Redis (lokálně soubor `.data/store.json`).

## Lokálně
```
npm install
npm run dev                  # http://localhost:3000 (bez hesla, data v .data/store.json)
```
Nebo dvojklik na `spustit-simulator.bat`. Podmínky brokera z MT5: `python export_broker_conditions.py`.

## Kontroly
```
npx tsx scripts/test-sim.ts                      # broker: SL/TP, gap, swapy, velikost pozice
npx tsx scripts/compare-signals.ts <json>        # H1 signály TS vs Python
npx tsx scripts/compare-f2.ts <json>             # průraz F2 TS vs Python
```
