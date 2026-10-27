// Kontroly simulovaneho brokera. Pouziti: npx tsx scripts/test-sim.ts
import { MARKETS, spreadAt } from "../lib/markets";
import { findHit, lotsFor, swapBetween } from "../lib/sim";

let bad = 0;
const check = (name: string, ok: boolean) => {
  if (!ok) bad++;
  console.log(`${ok ? "OK   " : "CHYBA"} ${name}`);
};
const eu = MARKETS.EURUSD;
const t0 = Date.UTC(2026, 9, 26, 14, 0) / 1000; // pondeli 14:00 UTC
const half = spreadAt(eu, t0) / 2;
const bar = (i: number, o: number, h: number, l: number, c: number) => ({ time: t0 + i * 60, open: o, high: h, low: l, close: c });

// long 1.1000, SL 1.0950, TP 1.1100
let r = findHit(eu, "long", 1.095, 1.11, [bar(0, 1.1, 1.1, 1.1, 1.1), bar(1, 1.1, 1.102, 1.098, 1.101)], 60, t0, t0 + 600);
check("long bez zasahu", r.hit === null);
r = findHit(eu, "long", 1.095, 1.11, [bar(1, 1.1, 1.1101 + half, 1.099, 1.105)], 60, t0, t0 + 600);
check("long TP na bidu (high - pul spreadu)", r.hit?.reason === "TP" && r.hit.exit === 1.11);
r = findHit(eu, "long", 1.095, 1.11, [bar(1, 1.1, 1.1099 + half, 1.099, 1.105)], 60, t0, t0 + 600);
check("long TP o chlup nedosazen kvuli spreadu", r.hit === null);
r = findHit(eu, "long", 1.095, 1.11, [bar(1, 1.1, 1.12, 1.09, 1.1)], 60, t0, t0 + 600);
check("SL i TP v jedne svicce = SL", r.hit?.reason === "SL" && r.hit.exit === 1.095);
r = findHit(eu, "long", 1.095, 1.11, [bar(1, 1.09, 1.092, 1.088, 1.09)], 60, t0, t0 + 600);
check("gap pod SL -> plneni za horsi cenu", r.hit?.reason === "SL" && Math.abs(r.hit.exit - (1.09 - half)) < 1e-12);
r = findHit(eu, "short", 1.105, 1.09, [bar(1, 1.1, 1.1051 - half, 1.099, 1.1)], 60, t0, t0 + 600);
check("short SL na asku (high + pul spreadu)", r.hit?.reason === "SL");
r = findHit(eu, "long", 1.095, 1.11, [bar(0, 1.1, 1.2, 1.0, 1.1)], 60, t0 + 30, t0 + 600);
check("svicka otevreni se bere jen zaviraci cenou", r.hit === null);

// swapy: EURUSD long -5.95 bodu, 3x ve stredu
const day = 86400;
const mon = Date.UTC(2026, 9, 26, 15) / 1000;
const one = swapBetween(eu, "long", 1, mon, mon + day, 1.12);
check(`po->ut 1 noc (${one.toFixed(2)} $)`, Math.abs(one - eu.swapLong * 1.12 * eu.moneyPerPrice) < 1e-9);
const wed = swapBetween(eu, "long", 1, mon + 2 * day, mon + 3 * day, 1.12);
check("st->ct 3 noci (den brokera)", Math.abs(wed - 3 * one) < 1e-9);
const wkd = swapBetween(eu, "long", 1, mon + 4 * day, mon + 7 * day, 1.12);
check("pa->po jen patek 1x (vikend je ve strede)", Math.abs(wkd - one) < 1e-9);
check(`SPX500 trojity swap v patek (roll3=${MARKETS.SPX500mini.roll3})`, MARKETS.SPX500mini.roll3 === 4);

// velikost: 100k, 0.25 %, SL 50 pipu -> 250 $ / (0.005 * 100000) = 0.5 lotu
check("EURUSD 0.25 % pri SL 50 pipu = 0.5 lotu", lotsFor(eu, 1.1, 1.095, 0.25, 100000).lots === 0.5);
check("US30 pod minimem 1 lot", lotsFor(MARKETS.US30mini, 47000, 46000, 0.25, 100000).lots === null);
console.log(bad ? `\n${bad} CHYB` : "\nVSE OK");
process.exit(bad ? 1 : 0);
