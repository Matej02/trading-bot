// Indikatory pocitane stejne jako v pandas (bot v Pythonu), aby signaly sedely.

export type Series = (number | null)[];

/** ewm(span, adjust=False).mean() */
export function ema(x: number[], span: number): Series {
  const a = 2 / (span + 1);
  const out: Series = [];
  let prev: number | null = null;
  for (const v of x) {
    prev = prev == null ? v : a * v + (1 - a) * prev;
    out.push(prev);
  }
  return out;
}

/** rolling(n).mean() */
export function sma(x: Series, n: number): Series {
  return x.map((_, i) => {
    if (i < n - 1) return null;
    let s = 0;
    for (let j = i - n + 1; j <= i; j++) {
      const v = x[j];
      if (v == null) return null;
      s += v;
    }
    return s / n;
  });
}

/** rolling(n).std() s ddof=1 */
export function stdev(x: number[], n: number): Series {
  return x.map((_, i) => {
    if (i < n - 1) return null;
    const w = x.slice(i - n + 1, i + 1);
    const m = w.reduce((a, b) => a + b, 0) / n;
    return Math.sqrt(w.reduce((a, b) => a + (b - m) ** 2, 0) / (n - 1));
  });
}

/** rolling(n).median() */
export function rollingMedian(x: Series, n: number): Series {
  return x.map((_, i) => {
    if (i < n - 1) return null;
    const w = x.slice(i - n + 1, i + 1);
    if (w.some((v) => v == null)) return null;
    const s = (w as number[]).slice().sort((a, b) => a - b);
    return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  });
}

/** rolling(n).rank(pct=True) - poradi posledni hodnoty v okne (shody prumerem) */
export function rollingRankPct(x: Series, n: number): Series {
  return x.map((v, i) => {
    if (i < n - 1 || v == null) return null;
    let less = 0, equal = 0;
    for (let j = i - n + 1; j <= i; j++) {
      const w = x[j];
      if (w == null) return null;
      if (w < v) less++;
      else if (w === v) equal++;
    }
    return (less + (equal + 1) / 2) / n;
  });
}

/** ATR = rolling(n).mean() true range */
export function atr(high: number[], low: number[], close: number[], n = 14): Series {
  const tr = high.map((h, i) =>
    i === 0 ? h - low[i] : Math.max(h - low[i], Math.abs(h - close[i - 1]), Math.abs(low[i] - close[i - 1])),
  );
  // pandas: prvni TR ma shift NaN -> max ignoruje NaN, tedy h-l; stejne jako tady
  return sma(tr, n);
}

/** RSI (Wilderovo vyhlazeni) posledni svicky, null = malo dat. */
export function rsiLast(close: number[], n = 14): number | null {
  if (close.length <= n) return null;
  let up = 0, down = 0;
  for (let i = 1; i <= n; i++) {
    const d = close[i] - close[i - 1];
    if (d > 0) up += d;
    else down -= d;
  }
  up /= n;
  down /= n;
  for (let i = n + 1; i < close.length; i++) {
    const d = close[i] - close[i - 1];
    up = (up * (n - 1) + Math.max(d, 0)) / n;
    down = (down * (n - 1) + Math.max(-d, 0)) / n;
  }
  return down === 0 ? 100 : 100 - 100 / (1 + up / down);
}
