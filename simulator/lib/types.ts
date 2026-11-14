import type { AiContext } from "./aiPrompt";
export type Dir = "long" | "short";
export type TF = "1m" | "5m" | "15m" | "1h" | "1d";

export const TF_SEC: Record<TF, number> = { "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 86400 };

/** time = zacatek svicky, unix sekundy UTC */
export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface Market {
  id: string;
  name: string;
  group: string;
  yahoo: string;
  binance: string | null;
  digits: number;
  pip: number;
  spreadByHour: number[]; // zivy spread brokera v cenovych jednotkach, index = hodina UTC
  swapLong: number; // podil ceny za noc (zaporne = platis)
  swapShort: number;
  roll3: number; // den trojiteho swapu, 0 = pondeli
  moneyPerPrice: number; // USD za pohyb ceny o 1.0 na 1 lot
  volMin: number;
  volStep: number;
  volMax: number;
  decisionHour: number;
  priceScale: number; // cena Yahoo x tohle = cena brokera (GAUUSD je v gramech, Yahoo v uncich)
  feedOnly?: boolean; // jen datovy zdroj pro vybrane systemy (napr. index z futures 23 h) - momentum ho neobchoduje
}

export interface Signal {
  id: string;
  system: string;
  market: string;
  dir: Dir;
  price: number; // cena v okamziku signalu (stred)
  time: number; // kdy signal vznikl (unix s)
  barTime: number; // svicka, ze ktere signal je
  sl: number;
  tp: number | null; // null = bez TP (momentum)
  reason: string;
  riskPct: number; // riziko u SL v % uctu
}

export type Vote = "ano" | "ne";

export interface Opinion {
  agent: string;
  role: string;
  vote: Vote;
  hard: boolean; // tvrde veto (NE = konec), jinak jen rada
  reason: string;
}

export interface Deliberation {
  id: string;
  signal: Signal;
  opinions: Opinion[];
  decision: "beru" | "neberu";
  summary: string;
  time: number;
  lots: number | null;
  positionId: string | null;
}

export interface Position {
  id: string;
  market: string;
  system: string;
  signalId: string;
  dir: Dir;
  lots: number;
  entry: number;
  sl: number;
  tp: number | null;
  openTime: number;
  swap: number;
  checkedTo: number; // do kdy uz jsou zkontrolovane SL/TP (unix s)
  expires?: number; // po tomhle case se zavre za trzni cenu (nejdelsi drzeni setupu)
}

export interface ClosedTrade extends Position {
  exit: number;
  closeTime: number;
  pnl: number; // bez swapu
  reason: string;
}

/** Stinovy obchod: kazdy signal (prijaty i zamitnuty) - jak by dopadl */
export interface Shadow {
  signalId: string;
  system: string;
  market: string;
  dir: Dir;
  taken: boolean;
  entry: number;
  sl: number;
  tp: number | null;
  openTime: number;
  checkedTo: number;
  r: number | null; // vysledek v nasobcich rizika, null = jeste bezi
  ai?: Vote | null; // hlas AI analytika (u starsich zaznamu chybi)
}

export interface Account {
  start: number;
  balance: number;
  dayStart: number;
  dayKey: string;
  peak: number;
  halted: string | null; // drawdown limit - challenge neprosla (data se sbiraji dal)
  pausedDay?: string | null; // den, kdy padl denni limit - ten den uz zive obchody nebere
  passed: boolean;
  lastRollover: string; // YYYY-MM-DD posledniho zapocitaneho swapu
}

export interface MomentumBook {
  dir: number;
  since: number;
  pending: boolean;
  attempts: number;
}

export interface LogEntry {
  t: number;
  text: string;
}

/** Kdo prave ridi bota (ostatni zarizeni jen sleduji) - plati do `until` (ms). */
export interface Lease {
  device: string;
  label: string;
  until: number;
}

/** Stav bez historie: ukada se na server jako jeden zaznam, historie zvlast (denik, obchody, stiny). */
/** Dotaz na AI analytika ve fronte: rozhodnuti padlo hned, posudek se k nemu dopise dodatecne. */
export interface AiJob { id: string; ctx: AiContext; at: number; tries: number }

export interface CoreState {
  version: 1;
  settings: Settings;
  broker: { account: Account; positions: Position[] };
  lastBar: Record<string, number>;
  momentum: { book: Record<string, MomentumBook>; lastRun: Record<string, string> };
  seen: string[];
  aiQueue?: AiJob[];
}

export interface LoadResult {
  db: "upstash" | "soubor";
  auth: "open" | "password";
  core: CoreState | null;
  journal: Deliberation[]; // nejnovejsi prvni
  journalTotal: number;
  closed: ClosedTrade[]; // nejnovejsi prvni
  shadows: Shadow[];
  log: LogEntry[]; // nejnovejsi prvni
  lease: Lease | null;
  now: number;
  serverTick: { at: number; msg: string } | null; // posledni beh bota na serveru (24/7)
  rev: number; // cislo verze ulozeneho stavu (kazde ulozeni +1)
}

/** Odpoved na ulozeni. stale = mezitim ulozil nekdo jiny, zmeny se nezapsaly (zastaraly stav). */
export interface SaveResult {
  ok: boolean;
  lease: Lease | null;
  rev?: number;
  stale?: boolean;
}

export interface SaveBody {
  device: string;
  label: string;
  takeover?: boolean; // prevzit rizeni od jineho zarizeni
  reset?: boolean; // smazat vse a zacit znovu
  baseRev?: number; // verze stavu, ze ktere zarizeni vychazi (jina nez na serveru = zastaraly stav)
  core?: CoreState;
  journalNew?: Deliberation[];
  journalUpd?: Deliberation[];
  shadowsNew?: Shadow[];
  shadowsUpd?: Shadow[];
  closed?: ClosedTrade[]; // chronologicky
  log?: LogEntry[]; // chronologicky
}

export interface Settings {
  botOn: boolean;
  /** "vse" = bere kazdy obchod, ktery projde tvrdymi kontrolami; "opatrny" = rozhoduje i vetsina poradcu */
  mode: "vse" | "opatrny";
  follow: boolean; // graf skace na trh noveho obchodu
  statistikBlocks: boolean; // false = v simulaci jen radi
  riskPct: number; // riziko na obchod u bar strategii
  dailyLossPct: number; // denni limit ztraty - po zasahu jen sber dat do konce dne
  rrr: number; // pomer zisk : riziko, TP = rrr x vzdalenost SL
  ai: boolean; // AI analytik (Gemini) se k signalum vyjadruje
  aiVeto: "auto" | "nikdy"; // auto = NE od AI je veto, jakmile si to vyslouzi na zivych signalech (lib/aiScore.ts)
  maxTradesPerDay: number;
  maxOpen: number;
  systems: Record<string, boolean>;
}
