// Bot v prohlizeci: hlida uzavrene svicky, z nich signaly, agenti rozhodnou, simulovany broker
// obchoduje. Stav se uklada na server (po prihlaseni stejny na PC i mobilu, cely denik);
// bez databaze jen do localStorage tohoto prohlizece. Bota ridi vzdy jen jedno zarizeni,
// ostatni sleduji. Po pauze se pozice dopocitaji ze svicek (SL/TP, swapy).
import { AI_AGENT, codeOpinions, judge, type AgentCtx } from "./agents";
import { aiScore } from "./aiScore";
import type { AiContext } from "./aiPrompt";
import { blockedBy, decisionVerdict } from "./verdict";
import { ema, rsiLast } from "./indicators";
import { closedCandles, nowSec, store } from "./data";
import { isCrypto, MARKET_IDS, MARKETS, quote } from "./markets";
import { apiLogout, apiRelease, browserBackend, deviceInfo, type Backend } from "./remote";
import { eventsFor, inMinutes, releasesFor, releaseText, type CalEvent, type Release } from "./calendar";
import {
  closePosition, DAILY_LOSS_DEFAULT, dayKey, equity, exitPrice, findHit, freshBroker, lotsFor, openPosition, swapBetween,
  updateAccount, dailyLimitOf, propLimitsOn, type BrokerState,
} from "./sim";
import {
  barSignal, barStatus, dailyCloses, lastAtr, MANUAL, manualLevels, MOM_RISK_PCT, MOM_SL_SIGMA, momentumReturn,
  momentumTarget, relVol, SYSTEM, SYSTEMS, type SystemDef, type Tone,
} from "./strategies";
import type {
  AiJob, Candle, ClosedTrade, CoreState, Deliberation, Lease, LoadResult, LogEntry, MomentumBook, Opinion, Position, SaveBody,
  Settings, Shadow, Signal, TF,
} from "./types";
import { TF_SEC } from "./types";

const STORAGE_KEY = "tradingSim.v1";
const START_BALANCE = 100000;
const MOMENTUM = "momentum_d1_L250";
const POLL: Record<TF, number> = { "1m": 8, "5m": 20, "15m": 30, "1h": 60, "1d": 1800 };
const CORE_EVERY_MS = 60_000; // stav (pozice, posledni svicky) se uklada nejpozdeji po minute
const VIEW_EVERY_MS = 60_000; // sledujici zarizeni se obnovuje jednou za minutu

export interface BotState {
  version: 1;
  settings: Settings;
  broker: BrokerState;
  journal: Deliberation[]; // v pameti jen poslednich 300, na serveru vse
  shadows: Shadow[];
  lastBar: Record<string, number>;
  momentum: { book: Record<string, MomentumBook>; lastRun: Record<string, string> };
  seen: string[];
  log: LogEntry[];
  aiQueue: AiJob[];
}

const AI_GAP_MS = 5000; // server pusti nejvys 12 dotazu za minutu
const AI_LATE = " (AI analytik: posudek dopíše dodatečně.)";

export function freshState(): BotState {
  return {
    version: 1,
    settings: {
      botOn: false, mode: "vse", follow: true, statistikBlocks: false, riskPct: 0.25, maxTradesPerDay: 100, maxOpen: 50,
      dailyLossPct: DAILY_LOSS_DEFAULT, rrr: 2, ai: true, aiVeto: "auto", systems: Object.fromEntries(SYSTEMS.map((s) => [s.id, true])),
    },
    broker: freshBroker(START_BALANCE, nowSec()),
    journal: [], shadows: [], lastBar: {}, momentum: { book: {}, lastRun: {} }, seen: [], log: [], aiQueue: [],
  };
}

/** Doplni nastaveni ze starsich verzi. */
function migrate<T extends { settings: Settings }>(s: T): T {
  // nove strategie z novejsi verze se zapnou i v uz ulozenem stavu
  for (const sys of SYSTEMS) if (!(sys.id in s.settings.systems)) s.settings.systems[sys.id] = true;
  if (!s.settings.mode) {
    // stav z verze bez tlacitka AKTIVOVAT: bot stoji, dokud ho uzivatel nezapne
    Object.assign(s.settings, { botOn: false, mode: "vse", follow: true,
      maxTradesPerDay: Math.max(s.settings.maxTradesPerDay, 100), maxOpen: Math.max(s.settings.maxOpen, 50) });
  }
  s.settings.dailyLossPct ??= DAILY_LOSS_DEFAULT;
  s.settings.rrr ??= 2;
  s.settings.ai ??= true;
  s.settings.aiVeto ??= "auto";
  return s;
}

function loadLocal(): BotState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const s = raw ? (JSON.parse(raw) as BotState) : null;
    return s?.version === 1 ? migrate(s) : null;
  } catch {
    return null; // prazdne nebo nedostupne uloziste
  }
}

const coreOf = (s: BotState): CoreState => ({
  version: 1, settings: s.settings, broker: { account: s.broker.account, positions: s.broker.positions },
  lastBar: s.lastBar, momentum: s.momentum, seen: s.seen.slice(-500), aiQueue: s.aiQueue.slice(-60),
});

export interface RadarItem {
  system: string;
  market: string;
  text: string;
  tone: Tone | "err";
  t: number;
}

type Phase = "loading" | "login" | "import" | "ready" | "error";

interface Dirty {
  core: boolean;
  journal: Map<string, { d: Deliberation; isNew: boolean }>;
  shadows: Map<string, { x: Shadow; isNew: boolean }>;
  closed: ClosedTrade[];
  log: LogEntry[];
}
const noDirty = (): Dirty => ({ core: false, journal: new Map(), shadows: new Map(), closed: [], log: [] });

export class Bot {
  state: BotState = freshState();
  phase: Phase = "loading";
  /** server = data v databazi (po prihlaseni vsude stejna), local = jen v tomhle prohlizeci */
  mode: "server" | "local" = "local";
  /** runner = tohle zarizeni ridi bota, viewer = jen sleduje */
  role: "runner" | "viewer" = "runner";
  db = "";
  auth = ""; // "password" = je co odhlasit
  setupNote = ""; // proc bezi jen lokalne (no-db / no-password)
  syncNote = ""; // posledni problem s ukladanim
  journalTotal = 0;
  lease: Lease | null = null;
  serverTick: { at: number; msg: string } | null = null; // posledni beh bota na serveru
  importInfo: { balance: number; journal: number; closed: number } | null = null;
  status = "";
  aiNote = ""; // posledni problem AI analytika (zobrazi se v Nastaveni)
  private aiLast = 0;
  private aiDraining = false;
  private serverRun = false; // bot 24/7: frontu AI odbavi runServerTick (na serveru nic nebezi na pozadi)
  /** co bot prave sleduje, po strategiich a trzich (jen v pameti) */
  readonly radar = new Map<string, RadarItem>();
  private events: CalEvent[] | null = null; // ekonomicky kalendar - pristi zpravy (obnovuje se po 10 min)
  private releases: Release[] = []; // uz vyhlasene zpravy se skutecnou hodnotou
  private eventsAt = 0;

  constructor(private backend: Backend, readonly device: { id: string; label: string }) {}

  private listeners = new Set<() => void>();
  private busy = false;
  private syncing = false;
  private forceMomentum = false;
  private timer: ReturnType<typeof setInterval> | undefined;
  private viewTimer: ReturnType<typeof setInterval> | undefined;
  private dirty = noDirty();
  private resetNext = false; // pristi ulozeni nejdriv smaze vse na serveru (reset uctu)
  private lastCoreSave = 0;
  private lastFullLoad = 0;
  private hooked = false;

  // ---------------------------------------------------------- start, prihlaseni, role

  async init() {
    this.stopAll();
    this.phase = "loading";
    this.emit();
    const r = await this.backend.load(false);
    if (r.status === 401) return this.setPhase("login");
    if (r.status === 503) {
      // bez databaze (nebo bez hesla na serveru): bezi jako drive, jen v tomhle prohlizeci
      this.mode = "local";
      this.setupNote = r.data.error ?? "";
      this.state = loadLocal() ?? freshState();
      this.role = "runner";
      this.phase = "ready";
      this.startRunner();
      return;
    }
    if (r.status !== 200) {
      this.syncNote = r.data.error ?? `chyba ${r.status}`;
      return this.setPhase("error");
    }
    this.mode = "server";
    this.db = r.data.db ?? "";
    this.auth = r.data.auth ?? "";
    if (!r.data.core) {
      const local = loadLocal();
      if (local && (local.journal.length || local.broker.closed.length || local.broker.positions.length)) {
        this.importInfo = { balance: local.broker.account.balance, journal: local.journal.length, closed: local.broker.closed.length };
        return this.setPhase("import");
      }
      return this.startFresh();
    }
    this.apply(r.data as LoadResult, true);
    this.phase = "ready";
    const l = r.data.lease;
    if (!l || l.device === this.device.id || l.until < (r.data.now ?? Date.now())) this.startRunner();
    else this.startViewer();
  }

  private setPhase(p: Phase) {
    this.phase = p;
    this.emit();
  }

  /** Nacte data ze serveru do pameti (full = vcetne stinu a delsi historie). */
  private apply(r: LoadResult, full: boolean) {
    const core = migrate(r.core!);
    if (full) {
      this.state = {
        version: 1, settings: core.settings, broker: { account: core.broker.account, positions: core.broker.positions, closed: r.closed },
        journal: r.journal, shadows: r.shadows, lastBar: core.lastBar, momentum: core.momentum, seen: core.seen, log: r.log,
        aiQueue: core.aiQueue ?? [],
      };
      this.lastFullLoad = Date.now();
    } else {
      // sledujici zarizeni: stav vymenit, konec historie doplnit
      const s = this.state;
      Object.assign(s, { settings: core.settings, lastBar: core.lastBar, momentum: core.momentum, seen: core.seen, aiQueue: core.aiQueue ?? [] });
      s.broker.account = core.broker.account;
      s.broker.positions = core.broker.positions;
      const byId = new Map(s.journal.map((d) => [d.id, d]));
      r.journal.forEach((d) => byId.set(d.id, d));
      s.journal = [...byId.values()].sort((a, b) => b.time - a.time).slice(0, 300);
      const closedKey = (c: ClosedTrade) => `${c.id}|${c.closeTime}`;
      const known = new Set(s.broker.closed.map(closedKey));
      s.broker.closed = [...r.closed.filter((c) => !known.has(closedKey(c))), ...s.broker.closed].slice(0, 500);
      const sh = new Map(s.shadows.map((x) => [x.signalId, x]));
      r.shadows.forEach((x) => sh.set(x.signalId, x));
      s.shadows = [...sh.values()];
      const logKey = (l: LogEntry) => `${l.t}|${l.text}`;
      const knownLog = new Set(s.log.map(logKey));
      s.log = [...r.log.filter((l) => !knownLog.has(logKey(l))), ...s.log].slice(0, 200);
    }
    this.journalTotal = r.journalTotal;
    this.lease = r.lease;
    this.serverTick = r.serverTick ?? null;
  }

  private startRunner() {
    this.role = "runner";
    clearInterval(this.viewTimer);
    this.viewTimer = undefined;
    this.dirty.core = true; // prvni ulozeni zabere rizeni
    this.hookPage();
    if (!this.timer) {
      this.timer = setInterval(() => this.tick(), 5000);
      this.tick();
    }
    this.emit();
  }

  private startViewer() {
    this.role = "viewer";
    clearInterval(this.timer);
    this.timer = undefined;
    this.radar.clear();
    if (!this.viewTimer) this.viewTimer = setInterval(() => this.refreshView(), VIEW_EVERY_MS);
    this.emit();
  }

  private async refreshView() {
    if (typeof document !== "undefined" && document.hidden) return; // skryta karta nic nestahuje
    const full = Date.now() - this.lastFullLoad > 5 * 60_000;
    const r = await this.backend.load(!full);
    if (r.status === 401) return this.toLogin();
    if (r.status !== 200 || !r.data.core) return;
    this.apply(r.data as LoadResult, full);
    const l = r.data.lease;
    // zarizeni, ktere ridilo, zmizelo (lease vyprsel) -> rizeni prebira tohle
    if (!l || l.until < (r.data.now ?? Date.now())) this.startRunner();
    this.emit();
  }

  /** Sledujici zarizeni prevezme rizeni (to druhe pri dalsim ulozeni zjisti, ze uz neridi). */
  async takeOver() {
    if (this.mode !== "server" || this.role === "runner") return;
    const r = await this.backend.load(false);
    if (r.status === 200 && r.data.core) this.apply(r.data as LoadResult, true);
    const res = await this.backend.save({ device: this.device.id, label: this.device.label, takeover: true, core: coreOf(this.state) });
    if (res.status === 200) {
      this.lease = res.data.lease ?? null;
      this.lastCoreSave = Date.now();
      this.startRunner();
    } else {
      this.syncNote = res.data.error ?? `převzetí se nepovedlo (${res.status})`;
      this.emit();
    }
  }

  /**
   * Jeden beh bota na serveru (budi ho cron kazdych 5 min). Ridi jen tehdy, kdyz zrovna neridi
   * zadny prohlizec - otevrena stranka ma prednost, po jejim zavreni prebira server.
   */
  async runServerTick(): Promise<string> {
    const r = await this.backend.load(false);
    if (r.status !== 200) return `chyba načtení: ${r.data.error ?? r.status}`;
    if (!r.data.core) return "na serveru zatím není účet – nejdřív se přihlas na stránce";
    const l = r.data.lease;
    if (l && l.device !== this.device.id && l.until > (r.data.now ?? Date.now())) return `řídí ${l.label}, server čeká`;
    this.mode = "server";
    this.db = r.data.db ?? "";
    this.apply(r.data as LoadResult, true);
    this.phase = "ready";
    this.role = "runner";
    this.dirty.core = true; // ulozeni na konci zabere rizeni
    this.serverRun = true;
    const t0 = Date.now();
    await this.tick();
    // fronta AI ve zbytku casu (beh ma limit 60 s)
    await this.drainAi(45_000 - (Date.now() - t0));
    await this.sync();
    const s = this.state;
    return `bot ${s.settings.botOn ? "běží" : "je vypnutý"}, ${s.broker.positions.length} pozic, balance ${s.broker.account.balance.toFixed(2)} $`;
  }

  /** Prvni prihlaseni: nahrat ucet a denik z tohoto prohlizece na server. */
  async importLocal() {
    const local = loadLocal();
    if (!local) return this.startFresh();
    this.setPhase("loading");
    const base = { device: this.device.id, label: this.device.label, takeover: true };
    const chunks = <T>(a: T[], n: number) => Array.from({ length: Math.ceil(a.length / n) }, (_, i) => a.slice(i * n, i * n + n));
    const batches: SaveBody[] = [
      { ...base, reset: true, core: coreOf(local) },
      ...chunks([...local.journal].reverse(), 100).map((j) => ({ ...base, journalNew: j })),
      ...chunks(local.shadows, 300).map((x) => ({ ...base, shadowsNew: x })),
      ...chunks([...local.broker.closed].reverse(), 200).map((c) => ({ ...base, closed: c })),
      ...chunks([...local.log].reverse(), 200).map((l) => ({ ...base, log: l })),
    ];
    for (const b of batches) {
      const r = await this.backend.save(b);
      if (r.status !== 200) {
        this.syncNote = `nahrání se nepovedlo: ${r.data.error ?? r.status}`;
        return this.setPhase("error");
      }
    }
    await this.init();
  }

  /** Cisty ucet 100 000 $ na serveru. */
  startFresh() {
    this.state = freshState();
    this.markAllDirty(true);
    this.phase = "ready";
    this.startRunner();
  }

  async logout() {
    if (this.mode === "server" && this.role === "runner") await this.sync({ force: true });
    if (this.mode === "server" && this.role === "runner") apiRelease(this.device.id);
    await apiLogout();
    this.toLogin();
  }

  private toLogin() {
    this.stopAll();
    this.phase = "login";
    this.emit();
  }

  private stopAll() {
    clearInterval(this.timer);
    clearInterval(this.viewTimer);
    this.timer = undefined;
    this.viewTimer = undefined;
  }

  stop() {
    this.stopAll();
  }

  /** Pri zavreni stranky posledni ulozeni a uvolneni rizeni; pri skryti aspon ulozit. */
  private hookPage() {
    if (this.hooked || typeof window === "undefined") return;
    this.hooked = true;
    window.addEventListener("pagehide", () => {
      if (this.mode !== "server" || this.role !== "runner") return;
      apiRelease(this.device.id, this.takeDirty());
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden && this.mode === "server" && this.role === "runner") this.sync({ force: true, keepalive: true });
      if (!document.hidden && this.role === "viewer") this.refreshView();
    });
  }

  // ---------------------------------------------------------- ukladani

  on(fn: () => void) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit() {
    this.listeners.forEach((fn) => fn());
  }

  private markAllDirty(reset = false) {
    const s = this.state;
    this.dirty = {
      core: true,
      journal: new Map([...s.journal].reverse().map((d) => [d.id, { d, isNew: true }])),
      shadows: new Map(s.shadows.map((x) => [x.signalId, { x, isNew: true }])),
      closed: [...s.broker.closed].reverse(),
      log: [...s.log].reverse(),
    };
    this.resetNext = reset;
  }

  private recordJournal(d: Deliberation, isNew: boolean) {
    const was = this.dirty.journal.get(d.id);
    this.dirty.journal.set(d.id, { d, isNew: isNew || !!was?.isNew });
    this.dirty.core = true;
  }

  private recordShadow(x: Shadow, isNew: boolean) {
    const was = this.dirty.shadows.get(x.signalId);
    this.dirty.shadows.set(x.signalId, { x, isNew: isNew || !!was?.isNew });
  }

  /** Vezme neulozene zmeny jako davku k odeslani (a vycisti je). */
  private takeDirty(): SaveBody {
    const d = this.dirty;
    this.dirty = noDirty();
    const body: SaveBody = {
      device: this.device.id, label: this.device.label, core: coreOf(this.state), reset: this.resetNext || undefined,
      journalNew: [...d.journal.values()].filter((e) => e.isNew).map((e) => e.d),
      journalUpd: [...d.journal.values()].filter((e) => !e.isNew).map((e) => e.d),
      shadowsNew: [...d.shadows.values()].filter((e) => e.isNew).map((e) => e.x),
      shadowsUpd: [...d.shadows.values()].filter((e) => !e.isNew).map((e) => e.x),
      closed: d.closed, log: d.log,
    };
    this.resetNext = false;
    return body;
  }

  /** Neodeslane zmeny vrati zpet (pri chybe spojeni se poslou priste). */
  private restoreDirty(b: SaveBody) {
    const d = this.dirty;
    d.core = true;
    for (const e of b.journalNew ?? []) if (!d.journal.has(e.id)) d.journal.set(e.id, { d: e, isNew: true });
    for (const e of b.journalUpd ?? []) if (!d.journal.has(e.id)) d.journal.set(e.id, { d: e, isNew: false });
    for (const x of b.shadowsNew ?? []) if (!d.shadows.has(x.signalId)) d.shadows.set(x.signalId, { x, isNew: true });
    for (const x of b.shadowsUpd ?? []) if (!d.shadows.has(x.signalId)) d.shadows.set(x.signalId, { x, isNew: false });
    d.closed = [...(b.closed ?? []), ...d.closed];
    d.log = [...(b.log ?? []), ...d.log];
    if (b.reset) this.resetNext = true;
  }

  private async sync(opts: { force?: boolean; keepalive?: boolean } = {}) {
    if (this.mode === "local") return this.saveLocal();
    if (this.role !== "runner" || this.syncing) return;
    // udalosti (obchod, rozhodnuti, nastaveni) hned; bezne zmeny (kontrola SL/TP, svicky) jednou za minutu
    const d = this.dirty;
    const pending = d.core || d.journal.size || d.shadows.size || d.closed.length || d.log.length;
    if (!opts.force && !pending && Date.now() - this.lastCoreSave < CORE_EVERY_MS) return;
    const body = this.takeDirty();
    this.syncing = true;
    const r = await this.backend.save(body, opts.keepalive);
    this.syncing = false;
    if (r.status === 200) {
      this.lastCoreSave = Date.now();
      this.lease = r.data.lease ?? null;
      this.syncNote = "";
      if (body.journalNew?.length) this.journalTotal += body.journalNew.length;
    } else if (r.status === 409) {
      // bota mezitim prevzalo jine zarizeni - tady uz jen sledovat
      this.lease = r.data.lease ?? null;
      this.startViewer();
      await this.refreshView();
    } else if (r.status === 401) {
      this.restoreDirty(body);
      this.toLogin();
    } else {
      this.restoreDirty(body);
      this.syncNote = `neuloženo (${r.data.error ?? r.status}) – zkusím znovu`;
    }
    this.emit();
  }

  private saveLocal() {
    this.dirty = noDirty(); // lokalne se uklada cely stav, sledovani zmen netreba
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
    } catch {
      /* plne nebo zakazane uloziste - simulace bezi dal jen v pameti */
    }
  }

  /** Zmena z UI (nastaveni, zavreni pozice...) - jen na zarizeni, ktere ridi. */
  update(fn: (s: BotState) => void) {
    if (this.role === "viewer") return;
    fn(this.state);
    this.dirty.core = true;
    this.sync();
    this.emit();
  }

  /** Tlacitko AKTIVOVAT / ZASTAVIT. Aktivace = rezim "bere co jde". */
  activate(on: boolean) {
    if (this.role === "viewer") return;
    this.update((s) => {
      s.settings.botOn = on;
      if (on) s.settings.mode = "vse";
    });
    this.log(on ? "AKTIVOVÁNO – bot bere každý obchod, který projde tvrdými kontrolami." : "Bot zastaven.");
    if (on) this.tick();
  }

  reset() {
    if (this.role === "viewer") return;
    this.state = freshState();
    this.markAllDirty(true);
    this.journalTotal = 0;
    this.sync({ force: true });
    this.emit();
  }

  log(text: string) {
    const e = { t: nowSec(), text };
    this.state.log.unshift(e);
    if (this.state.log.length > 200) this.state.log.length = 200;
    this.dirty.log.push(e);
  }

  equityNow() {
    return equity(this.state.broker, store.lastPrice, nowSec());
  }

  /** Momentum hned pro vsechny trhy (bez ohledu na hodinu) - provede nejblizsi tick. */
  requestMomentum() {
    if (this.role === "viewer") return;
    this.forceMomentum = true;
    this.tick();
  }

  // ---------------------------------------------------------- hlavni smycka

  async tick() {
    if (this.busy || this.role !== "runner" || this.phase !== "ready") return;
    this.busy = true;
    const force = this.forceMomentum;
    this.forceMomentum = false;
    try {
      const now = nowSec();
      const s = this.state;
      if (Date.now() - this.eventsAt > 600_000) {
        const cal = await this.backend.calendar();
        if (cal) [this.events, this.releases] = [cal.events ?? this.events, cal.releases];
        this.eventsAt = Date.now();
      }
      await this.updatePositions(now);
      // i po zasahu limitu se signaly dal vyhodnocuji (Risk zive obchody vetuje) - sbiraji se data
      if (s.settings.botOn) {
        for (const sys of SYSTEMS) {
          if (!s.settings.systems[sys.id] || sys.kind !== "bar") continue;
          for (const id of sys.markets) {
            try {
              await this.runBarSystem(sys.id, id, now);
            } catch (e) {
              this.radar.set(`${sys.id}|${id}`, { system: sys.id, market: id, text: `chyba dat: ${(e as Error).message}`, tone: "err", t: now });
            }
          }
        }
        if (s.settings.systems[MOMENTUM]) await this.runMomentum(now, force);
      }
      for (const [k, item] of this.radar) {
        if (!s.settings.botOn || !s.settings.systems[item.system]) this.radar.delete(k);
      }
      if (s.settings.systems[MOMENTUM] && s.settings.botOn) this.momentumRadar(now);
      const eq = this.equityNow();
      const a = s.broker.account;
      const was = { passed: a.passed, day: a.dayKey };
      const { hit } = updateAccount(s.broker, eq, now, dailyLimitOf(s.settings), propLimitsOn(s.settings));
      if (hit || was.passed !== a.passed || was.day !== a.dayKey) this.dirty.core = true;
      if (hit) {
        this.log(`${hit} – zavírám pozice, živé obchody stop, signály dál sbírám do statistiky.`);
        for (const p of [...s.broker.positions]) this.closeAtMarket(p.id, "limit ztráty");
      }
    } finally {
      this.busy = false;
      this.emit();
    }
    await this.sync();
    this.kickAi();
  }

  // ---------------------------------------------------------- pozice a stiny

  private close(p: Position, exit: number, t: number, reason: string) {
    const c = closePosition(this.state.broker, p, exit, t, reason);
    this.dirty.closed.push(c);
    this.dirty.core = true;
    return c;
  }

  private async updatePositions(now: number) {
    const s = this.state;
    const open = s.shadows.filter((x) => x.r == null);
    const markets = new Set([...s.broker.positions.map((p) => p.market), ...open.map((x) => x.market)]);
    for (const id of markets) {
      const m = MARKETS[id];
      const fast = s.broker.positions.some((p) => p.market === id && p.system !== MOMENTUM) ||
        open.some((x) => x.market === id && x.system !== MOMENTUM);
      const oldest = Math.min(...s.broker.positions.filter((p) => p.market === id).map((p) => p.checkedTo),
        ...open.filter((x) => x.market === id).map((x) => x.checkedTo));
      // po delsi pauze (zavrena stranka) se dopocita z hodinovych svicek, jinak minutove
      const tf: TF = !fast || now - oldest > 20 * 3600 ? "1h" : "1m";
      let candles: Candle[];
      try {
        // momentum drzi mesice a pojistny SL je 10 sigma daleko - staci kontrola jednou za hodinu
        candles = await store.get(m, tf, fast ? 10 : 3600);
      } catch {
        continue;
      }
      const mid = store.lastPrice.get(id)?.mid;
      for (const p of s.broker.positions.filter((x) => x.market === id)) {
        const { hit, checkedTo } = findHit(m, p.dir, p.sl, p.tp, candles, TF_SEC[tf], p.checkedTo, now);
        const to = hit ? hit.time : checkedTo;
        if (mid != null) {
          const sw = swapBetween(m, p.dir, p.lots, p.checkedTo, to, mid);
          if (sw) {
            p.swap += sw;
            this.dirty.core = true;
          }
        }
        p.checkedTo = Math.max(p.checkedTo, to);
        if (hit) {
          const c = this.close(p, hit.exit, Math.max(hit.time, p.openTime), hit.reason);
          this.log(`${hit.reason} ${c.market} ${c.dir} ${c.lots} lotu: ${(c.pnl + c.swap).toFixed(2)} $`);
        } else if (p.expires && now >= p.expires && mid != null) {
          const c = this.close(p, exitPrice(p, mid, now), now, "čas");
          this.log(`Konec doby držení ${c.market} ${c.dir}: ${(c.pnl + c.swap).toFixed(2)} $`);
        }
      }
      for (const x of open.filter((y) => y.market === id)) {
        const { hit, checkedTo } = findHit(m, x.dir, x.sl, x.tp, candles, TF_SEC[tf], x.checkedTo, now);
        x.checkedTo = Math.max(x.checkedTo, checkedTo);
        const sys = SYSTEM[x.system];
        const expires = sys?.maxHoldBars ? x.openTime + sys.maxHoldBars * TF_SEC[sys.tf] * (isCrypto(m) ? 1 : 7 / 5) : null;
        if (hit) {
          x.r = ((hit.exit - x.entry) * (x.dir === "long" ? 1 : -1)) / Math.abs(x.entry - x.sl);
        } else if (expires && now >= expires && mid != null) {
          // stejne jako skutecny obchod: po nejdelsi dobe drzeni ven za trzni cenu
          const q = quote(m, mid, now);
          x.r = (((x.dir === "long" ? q.bid : q.ask) - x.entry) * (x.dir === "long" ? 1 : -1)) / Math.abs(x.entry - x.sl);
        }
        if (x.r != null) {
          this.recordShadow(x, false);
          this.logVerdict(x);
        }
      }
    }
    // v pameti jen posledni stiny (na serveru zustavaji vsechny)
    if (s.shadows.length > 1000) s.shadows = s.shadows.filter((x, i) => x.r == null || i > s.shadows.length - 800);
  }

  closeAtMarket(positionId: string, reason = "ručně") {
    if (this.role === "viewer") return;
    const s = this.state;
    const p = s.broker.positions.find((x) => x.id === positionId);
    const px = p && store.lastPrice.get(p.market);
    if (!p || !px) return;
    const now = nowSec();
    p.swap += swapBetween(MARKETS[p.market], p.dir, p.lots, p.checkedTo, now, px.mid);
    const c = this.close(p, exitPrice(p, px.mid, now), now, reason);
    this.log(`Zavřeno (${reason}) ${c.market} ${c.dir}: ${(c.pnl + c.swap).toFixed(2)} $`);
  }

  // ---------------------------------------------------------- signaly

  private todayTrades(now: number) {
    const day = dayKey(now);
    return this.state.journal.filter((d) => d.decision === "beru" && dayKey(d.time) === day).length;
  }

  /** Zpetne do logu: jak by dopadl signal a jestli bylo rozhodnuti dobre (i u nevzatych). */
  private logVerdict(x: Shadow) {
    const d = this.state.journal.find((j) => j.id === x.signalId);
    if (!d || x.r == null) return;
    const v = decisionVerdict(d, x.r);
    const who = blockedBy(d);
    this.log(`Zpětně: ${d.decision === "beru" ? "BERU" : "NEBERU"} ${SYSTEM[x.system]?.name ?? x.system} ${x.market} ${x.dir} ` +
      `→ ${x.r >= 0 ? "+" : ""}${x.r.toFixed(2)} R – ${v.text}${who.length ? ` (zastavil: ${who.join(", ")})` : ""}.`);
  }

  private async handleSignal(sig: Signal, candles: Candle[], system: SystemDef = SYSTEM[sig.system]): Promise<Deliberation> {
    const s = this.state;
    const m = MARKETS[sig.market];
    const ctx: AgentCtx = {
      market: m, signal: sig, system, now: nowSec(), mid: store.lastPrice.get(sig.market)?.mid ?? sig.price, candles,
      broker: s.broker, equity: this.equityNow(), settings: s.settings, seen: new Set(s.seen),
      delayedMin: store.delayed.get(sig.market) ?? 0, todayTrades: this.todayTrades(nowSec()),
      systemTrades: s.broker.closed.filter((c) => c.system === sig.system), events: this.events, releases: this.releases,
    };
    s.seen.push(sig.id); // hned, aby stejny signal behem cekani na AI nesel podruhe
    if (s.seen.length > 2000) s.seen = s.seen.slice(-1500);
    const base = codeOpinions(ctx);
    // AI jen radi -> rozhodnuti hned a posudek se dopise z fronty; ceka se jen, kdyz si AI vyslouzilo veto
    let ai: { op: Opinion | null; note: string } = { op: null, note: "" };
    const vetoEarned = s.settings.aiVeto === "auto" && aiScore(s.shadows).earned;
    if (s.settings.ai && this.mode === "server") {
      const actx = this.aiContext(sig, system, candles, base.opinions, ctx.mid);
      if (vetoEarned) ai = await this.askAiNow(actx);
      else {
        s.aiQueue.push({ id: sig.id, ctx: actx, at: Date.now(), tries: 0 });
        ai.note = AI_LATE;
      }
    }
    // NE od AI je tvrde veto, jen kdyz si to AI vyslouzilo na zivych signalech (lib/aiScore.ts)
    if (ai.op?.vote === "ne" && vetoEarned) {
      ai.op = { ...ai.op, hard: true, role: `${ai.op.role} · veto (vysloužené)` };
    }
    const v = judge(ctx, ai.op ? [...base.opinions, ai.op] : base.opinions, base.lots, ai.note);
    const now = nowSec();
    const mid = store.lastPrice.get(sig.market)?.mid ?? ctx.mid;
    let positionId: string | null = null;
    if (v.decision === "beru" && v.lots) {
      const p = openPosition(s.broker, sig, v.lots, mid, now);
      // nejdelsi drzeni jako v testu (svicky -> dny; mimo krypto 5 obchodnich dni = 7 kalendarnich)
      if (system.maxHoldBars) p.expires = now + system.maxHoldBars * TF_SEC[system.tf] * (isCrypto(m) ? 1 : 7 / 5);
      positionId = p.id;
    }
    const d: Deliberation = { id: sig.id, signal: sig, opinions: v.opinions, decision: v.decision, summary: v.summary,
      time: now, lots: v.lots, positionId };
    s.journal.unshift(d);
    if (s.journal.length > 300) s.journal.length = 300;
    this.recordJournal(d, true);
    const q = quote(m, mid, now);
    const shadow: Shadow = { signalId: sig.id, system: sig.system, market: sig.market, dir: sig.dir, taken: v.decision === "beru",
      entry: sig.dir === "long" ? q.ask : q.bid, sl: sig.sl, tp: sig.tp, openTime: now, checkedTo: now, r: null,
      ai: ai.op?.vote ?? null };
    s.shadows.push(shadow);
    this.recordShadow(shadow, true);
    this.log(`${SYSTEM[sig.system].name} ${sig.market} ${sig.dir}: ${v.summary}`);
    return d;
  }

  /**
   * AI analytik (Gemini pres server): dostane signal, trend, volatilitu, spread vuci SL, zpravy a nazory
   * ostatnich agentu. Kontext se sklada hned pri signalu (posudek muze prijit z fronty pozdeji).
   */
  private aiContext(sig: Signal, system: SystemDef, candles: Candle[], opinions: Opinion[], mid: number): AiContext {
    const s = this.state;
    const m = MARKETS[sig.market];
    const close = candles.map((c) => c.close);
    const lastOf = (a: (number | null)[]) => (a.length ? a[a.length - 1] : null);
    const slDist = Math.abs(sig.price - sig.sl) || 1e-12;
    const spread = quote(m, mid, nowSec()).spread;
    const tail = candles.slice(-40);
    const done = s.shadows.filter((x) => x.system === sig.system && x.r != null);
    return {
      market: m.id, marketName: m.name, systemName: system.name, tf: system.tf, dir: sig.dir, price: sig.price,
      sl: sig.sl, tp: sig.tp, rrr: sig.tp == null ? null : Math.abs(sig.tp - sig.price) / slDist, spread,
      spreadPctOfSl: (spread / slDist) * 100, atr: lastAtr(candles), ema20: lastOf(ema(close, 20)), ema50: lastOf(ema(close, 50)),
      ema200: close.length >= 200 ? lastOf(ema(close, 200)) : null, rsi14: rsiLast(close, 14),
      closes: tail.map((c) => c.close), rangeHigh: Math.max(...tail.map((c) => c.high)), rangeLow: Math.min(...tail.map((c) => c.low)),
      reason: sig.reason, opinions: opinions.map((o) => ({ agent: o.agent, vote: o.vote, reason: o.reason })),
      dailyLossPct: Math.max(0, ((s.broker.account.dayStart - this.equityNow()) / s.broker.account.start) * 100),
      dailyLimitPct: dailyLimitOf(s.settings), openPositions: s.broker.positions.length,
      history: done.length ? { n: done.length, winrate: (done.filter((x) => x.r! > 0).length / done.length) * 100,
        avgR: done.reduce((a, x) => a + x.r!, 0) / done.length } : null,
      digits: m.digits,
      events: this.events ? eventsFor(this.events, m, nowSec(), nowSec() + 86400, ["High", "Medium"])
        .slice(0, 6).map((e) => `${e.currency} ${e.title} (${e.impact === "High" ? "vysoký" : "střední"} dopad) za ${inMinutes(e.time - nowSec())}`) : [],
      released: releasesFor(this.releases, m, nowSec() - 86400, nowSec()).slice(0, 8)
        .map((e) => `${releaseText(e)} (${e.impact === "High" ? "vysoký" : "střední"} dopad, před ${inMinutes(nowSec() - e.time)})`),
    };
  }

  /** Jeden dotaz na AI (nejvys jeden za 5 s). */
  private async callAi(actx: AiContext): Promise<{ op: Opinion | null; status: number }> {
    const wait = this.aiLast + AI_GAP_MS - Date.now();
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    this.aiLast = Date.now();
    const r = await this.backend.ai(actx);
    if (r.status !== 200 || !r.data.vote) {
      this.aiNote = r.data.error ?? `chyba ${r.status}`;
      return { op: null, status: r.status };
    }
    this.aiNote = "";
    const a = r.data;
    const risks = a.risks?.length ? ` Rizika: ${a.risks.join("; ")}.` : "";
    const op: Opinion = { agent: AI_AGENT, role: `Gemini · jistota ${a.confidence ?? 0} %${a.news ? ` · ${a.news} titulků` : ""}`,
      vote: a.vote === "ano" ? "ano" : "ne", hard: false, reason: `${a.reason}${risks}` };
    return { op, status: 200 };
  }

  /** Posudek hned (kdyz ma AI vyslouzene veto, rozhodnuti na nej musi pockat). */
  private async askAiNow(actx: AiContext) {
    const { op } = await this.callAi(actx);
    return { op, note: op ? "" : ` (AI analytik: nedostupný – ${this.aiNote}.)` };
  }

  /**
   * Odbavi frontu AI: po jednom dotazu za 5 s, dokud zbyva cas. Posudek se dopise k rozhodnuti v deniku
   * a ke stinovemu obchodu (skore AI). Vycerpany limit -> zkusi se pozdeji; starsi nez 2 h se zahodi.
   */
  private async drainAi(budgetMs: number) {
    const s = this.state;
    const end = Date.now() + budgetMs;
    const before = s.aiQueue.length;
    s.aiQueue = s.aiQueue.filter((j) => Date.now() - j.at < 2 * 3600_000);
    if (s.aiQueue.length !== before) this.dirty.core = true;
    while (s.aiQueue.length && this.role === "runner" && s.settings.ai) {
      if (Math.max(this.aiLast + AI_GAP_MS, Date.now()) + 18_000 > end) break; // na dalsi dotaz uz neni cas
      const job = s.aiQueue[0];
      const { op, status } = await this.callAi(job.ctx);
      if (status === 429) break; // limit - fronta pocka
      s.aiQueue.shift();
      this.dirty.core = true;
      if (!op) {
        if (++job.tries < 3) s.aiQueue.push(job);
        continue;
      }
      const d = s.journal.find((j) => j.id === job.id);
      if (d && !d.opinions.some((o) => o.agent === AI_AGENT)) {
        d.opinions.push(op);
        d.summary = d.summary.replace(AI_LATE, "") + ` (AI analytik dodatečně: ${op.vote.toUpperCase()}.)`;
        this.recordJournal(d, false);
      }
      const x = s.shadows.find((y) => y.signalId === job.id);
      if (x && !x.ai) {
        x.ai = op.vote;
        this.recordShadow(x, false);
      }
      this.emit();
    }
  }

  /** V prohlizeci bezi fronta AI na pozadi (tick na ni neceka). */
  private kickAi() {
    if (this.aiDraining || this.serverRun || !this.state.aiQueue.length || this.role !== "runner" || this.mode !== "server") return;
    this.aiDraining = true;
    this.drainAi(120_000).finally(() => {
      this.aiDraining = false;
      void this.sync();
    });
  }

  private async runBarSystem(systemId: string, id: string, now: number) {
    const sys = SYSTEM[systemId];
    const m = MARKETS[id];
    const closed = closedCandles(await store.get(m, sys.tf, POLL[sys.tf]), sys.tf, now);
    const key = `${systemId}|${id}`;
    // denni systemy potrebuji celou historii (tydenni EMA50), ostatnim staci 400 svicek
    const win = sys.tf === "1d" ? closed : closed.slice(-(sys.window ?? 400));
    const st = barStatus(systemId, win, m.digits);
    this.radar.set(key, { system: systemId, market: id, text: st.text, tone: st.tone, t: now });
    if (closed.length < 150) return;
    const last = closed[closed.length - 1];
    const prev = this.state.lastBar[key];
    this.state.lastBar[key] = last.time;
    // prvni beh si jen zapamatuje svicku - na starou svicku se neobchoduje
    if (prev == null || last.time <= prev) return;
    if (sys.exitRule) this.ruleExit(systemId, id, closed);
    const bs = barSignal(systemId, win);
    if (!bs) return;
    // cas signalu = uzavreni svicky (jako v Python botovi) - po otevreni stranky s pauzou
    // validator stary signal zamitne, misto aby se vstupovalo na zastaralou cenu
    // SL podle strategie, TP podle nastaveneho pomeru zisk : riziko
    const rrr = sys.rrr ?? this.state.settings.rrr;
    await this.handleSignal({
      id: `${systemId}-${id}-${last.time}`, system: systemId, market: id, dir: bs.dir, price: last.close,
      time: last.time + TF_SEC[sys.tf], barTime: last.time, sl: bs.sl,
      tp: sys.noTp ? null : last.close + (bs.dir === "long" ? 1 : -1) * rrr * Math.abs(last.close - bs.sl),
      reason: sys.noTp ? bs.reason : `${bs.reason} RRR 1:${rrr}.`, riskPct: this.state.settings.riskPct,
    }, closed);
  }

  /** Vystup podle pravidla strategie na zavreni svicky (napr. nad SMA5) - skutecne pozice i stinove obchody. */
  private ruleExit(systemId: string, id: string, closed: Candle[]) {
    const s = this.state;
    const sys = SYSTEM[systemId];
    const last = closed[closed.length - 1];
    if (sys.exitRule !== "sma5" || closed.length < 5) return;
    const sma5 = closed.slice(-5).reduce((a, c) => a + c.close, 0) / 5;
    const out = (dir: string) => (dir === "long" ? last.close > sma5 : last.close < sma5);
    const why = `zavření ${last.close > sma5 ? "nad" : "pod"} SMA5 ${sma5.toFixed(MARKETS[id].digits)}`;
    for (const p of s.broker.positions.filter((x) => x.system === systemId && x.market === id && x.openTime <= last.time + TF_SEC[sys.tf])) {
      if (out(p.dir)) this.closeAtMarket(p.id, why);
    }
    const px = store.lastPrice.get(id)?.mid;
    if (px == null) return;
    const now = nowSec();
    for (const x of s.shadows.filter((y) => y.system === systemId && y.market === id && y.r == null && y.openTime <= last.time + TF_SEC[sys.tf])) {
      if (!out(x.dir)) continue;
      const q = quote(MARKETS[id], px, now);
      x.r = (((x.dir === "long" ? q.bid : q.ask) - x.entry) * (x.dir === "long" ? 1 : -1)) / Math.abs(x.entry - x.sl);
      x.checkedTo = now;
      this.recordShadow(x, false);
      this.logVerdict(x);
    }
  }

  /** Rucni BUY/SELL z grafu: SL 1.5 ATR, TP 2.5 ATR podle zobrazeneho timeframu, rozhodnou agenti. */
  async manualSignal(marketId: string, tf: TF, dir: "long" | "short"): Promise<Deliberation | string> {
    if (this.role === "viewer") return "Bota teď řídí jiné zařízení – nejdřív převezmi řízení.";
    const m = MARKETS[marketId];
    const now = nowSec();
    const closed = closedCandles(await store.get(m, tf, 30), tf, now);
    const a = lastAtr(closed);
    const mid = store.lastPrice.get(marketId)?.mid;
    if (!a || mid == null) return "Na tomhle timeframu zatím není dost dat pro ATR.";
    const { sl, tp } = manualLevels(mid, a, dir, this.state.settings.rrr);
    const d = await this.handleSignal({
      id: `rucne-${marketId}-${now}`, system: MANUAL.id, market: marketId, dir, price: mid, time: now, barTime: now,
      sl, tp, riskPct: this.state.settings.riskPct,
      reason: `Ruční ${dir === "long" ? "nákup" : "prodej"} z grafu ${tf}, SL 1,5 ATR, RRR 1:${this.state.settings.rrr} (ATR ${a.toFixed(m.digits)}).`,
    }, closed, { ...MANUAL, tf });
    this.sync();
    this.emit();
    return d;
  }

  /**
   * Rucni obchod, ktery agenti zamitli jen radou (zadne tvrde veto): otevre se i tak,
   * rozhodnuti zustane v deniku jako NEBERU s poznamkou - stinove se porovna, kdo mel pravdu.
   */
  forceManual(deliberationId: string): string | null {
    if (this.role === "viewer") return "Bota teď řídí jiné zařízení – nejdřív převezmi řízení.";
    const s = this.state;
    const d = s.journal.find((x) => x.id === deliberationId);
    if (!d || d.signal.system !== MANUAL.id || d.positionId) return "Tenhle obchod už nejde otevřít.";
    const hard = d.opinions.find((o) => o.hard && o.vote === "ne");
    if (hard) return `Nejde – ${hard.agent} má tvrdé veto: ${hard.reason}`;
    const now = nowSec();
    if (now - d.time > 120) return "Signál je starší než 2 minuty – pošli nový.";
    const m = MARKETS[d.signal.market];
    const mid = store.lastPrice.get(m.id)?.mid;
    if (mid == null) return "Chybí aktuální cena.";
    const q = quote(m, mid, now);
    const { lots } = lotsFor(m, d.signal.dir === "long" ? q.ask : q.bid, d.signal.sl, d.signal.riskPct, s.broker.account.balance);
    if (!lots) return "Velikost pozice je pod minimem brokera.";
    const p = openPosition(s.broker, d.signal, lots, mid, now);
    d.positionId = p.id;
    d.lots = lots;
    d.summary += " → Otevřeno ručně i přes radu agentů.";
    this.recordJournal(d, false);
    this.log(`Ruční obchod ${m.id} ${d.signal.dir} otevřen přes nesouhlas poradců (${lots} lotu).`);
    this.sync();
    this.emit();
    return null;
  }

  /** Souhrn momenta do panelu: kolik trhu drzi a kdy je dalsi rozhodnuti. */
  private momentumRadar(now: number) {
    const s = this.state;
    const book = Object.values(s.momentum.book);
    const longs = book.filter((b) => b.dir > 0).length, shorts = book.filter((b) => b.dir < 0).length;
    const held = s.broker.positions.filter((p) => p.system === MOMENTUM).length;
    const hours = [...new Set(MARKET_IDS.map((id) => MARKETS[id].decisionHour))].sort((a, b) => a - b);
    let next = "";
    for (let add = 0; add < 8 && !next; add++) {
      for (const h of hours) {
        const t = new Date((Math.floor(now / 86400) + add) * 86400 * 1000 + h * 3600 * 1000);
        if (t.getTime() / 1000 > now && (t.getUTCDay() + 6) % 7 < 5) {
          next = t.toLocaleString("cs-CZ", { weekday: "long", hour: "2-digit", minute: "2-digit" });
          break;
        }
      }
    }
    const text = book.length
      ? `strategie chce ${longs}× long a ${shorts}× short, agenti pustili ${held} pozic · další rozhodnutí ${next}`
      : `zatím nerozhodovalo · další rozhodnutí ${next} (nebo tlačítkem v Nastavení)`;
    this.radar.set(`${MOMENTUM}|*`, { system: MOMENTUM, market: "40 trhů", text, tone: "wait", t: now });
  }

  // ---------------------------------------------------------- momentum

  /** Jednou denne v hodinu rozhodnuti (15:00 / 19:00 UTC), force = hned pro vsechny trhy. */
  private async runMomentum(now: number, force: boolean) {
    const s = this.state;
    const d = new Date(now * 1000);
    const day = dayKey(now);
    const weekday = (d.getUTCDay() + 6) % 7;
    const hours = [...new Set(MARKET_IDS.map((id) => MARKETS[id].decisionHour))];
    for (const h of hours) {
      const due = force || (weekday < 5 && d.getUTCHours() >= h && s.momentum.lastRun[h] !== day);
      if (!due) continue;
      s.momentum.lastRun[h] = day;
      this.dirty.core = true;
      const ids = MARKET_IDS.filter((id) => MARKETS[id].decisionHour === h);
      this.log(`Momentum: denní rozhodnutí pro ${ids.length} trhů (${h}:00 UTC)`);
      for (const id of ids) {
        try {
          await this.momentumMarket(id, now, day);
        } catch (e) {
          this.log(`Momentum ${id}: ${(e as Error).message}`);
        }
      }
    }
  }

  private async momentumMarket(id: string, now: number, day: string) {
    const s = this.state;
    const m = MARKETS[id];
    const candles = await store.get(m, "1d", 3600);
    const closes = dailyCloses(candles, isCrypto(m), now);
    if (closes.length < 251) return;
    const tgt = momentumTarget(closes);
    let book = s.momentum.book[id] ?? { dir: 0, since: 0, pending: false, attempts: 0 };
    if (tgt !== book.dir) {
      this.log(`Momentum ${id}: směr ${book.dir > 0 ? "+" : ""}${book.dir} → ${tgt > 0 ? "+" : ""}${tgt} (výnos za 250 dní ${(momentumReturn(closes) * 100).toFixed(1)} %)`);
      for (const p of s.broker.positions.filter((x) => x.market === id && x.system === MOMENTUM)) {
        this.closeAtMarket(p.id, "otočení trendu");
      }
      const px = store.lastPrice.get(id)?.mid;
      for (const x of s.shadows.filter((y) => y.market === id && y.system === MOMENTUM && y.r == null)) {
        if (px != null) {
          const q = quote(m, px, now);
          x.r = (((x.dir === "long" ? q.bid : q.ask) - x.entry) * (x.dir === "long" ? 1 : -1)) / Math.abs(x.entry - x.sl);
          this.recordShadow(x, false);
        }
      }
      book = { dir: tgt, since: now, pending: tgt !== 0, attempts: 0 };
    }
    const holding = s.broker.positions.some((x) => x.market === id && x.system === MOMENTUM);
    // ucici rezim: pozici, kterou drive zastavil Statistik nebo denni limit, zkusi znovu pri kazdem dennim rozhodnuti
    if (!book.pending && !holding && book.dir !== 0 && !s.settings.statistikBlocks) {
      book.pending = true;
      book.attempts = 0;
    }
    if (book.pending && !holding) {
      const dir = book.dir > 0 ? "long" : "short";
      const price = store.lastPrice.get(id)?.mid ?? closes[closes.length - 1];
      const dist = MOM_SL_SIGMA * relVol(closes) * price;
      const dailyCandles = candles.filter((c) => c.time < Math.floor(now / 86400) * 86400);
      const dlb = await this.handleSignal({
        id: `${MOMENTUM}-${id}-${day}`, system: MOMENTUM, market: id, dir, price, time: now, barTime: now,
        sl: dir === "long" ? price - dist : price + dist, tp: null, riskPct: MOM_RISK_PCT,
        reason: `Výnos za 250 obchodních dní ${(momentumReturn(closes) * 100).toFixed(1)} % → ${dir}. Bez TP, drží do otočení trendu.`,
      }, dailyCandles);
      book.attempts += 1;
      const finalVeto = dlb.opinions.some((o) => o.agent === "Statistik" && o.hard && o.vote === "ne");
      if (dlb.decision === "beru" || finalVeto || book.attempts >= 5) book.pending = false;
    }
    s.momentum.book[id] = book;
  }
}

let instance: Bot | null = null;
const g = globalThis as { __simBot?: Bot };
export function getBot() {
  if (!instance) {
    // po aktualizaci kodu za behu (vyvojova verze) by jinak dal tikal i stary bot a prepisoval stav
    g.__simBot?.stop();
    instance = new Bot(browserBackend, deviceInfo());
    g.__simBot = instance;
  }
  return instance;
}
