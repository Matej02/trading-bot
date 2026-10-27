// Skore AI analytika: jak dopadly signaly, ke kterym rekl ANO, proti tem, ke kterym rekl NE.
// AI se neda otestovat na minulych datech (historii zna), proto dostane pravo veta az tady,
// na zivych signalech - a jen kdyz jeho NE predem danym pravidlem opravdu predpovida horsi vysledek.
import type { Shadow } from "./types";

/** Pravidlo dane predem: aspon 30 vyhodnocenych signalu v kazde skupine, NE v prumeru ztratove
 *  a ANO lepsi nez NE s t >= 2 (Welchuv test, jednostranne ~98 %). */
export const AI_MIN_N = 30;
export const AI_MIN_T = 2;

interface Group { n: number; win: number; mean: number; sd: number }

function group(rs: number[]): Group {
  const n = rs.length;
  const mean = n ? rs.reduce((a, b) => a + b, 0) / n : 0;
  const sd = n > 1 ? Math.sqrt(rs.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1)) : 0;
  return { n, win: n ? (rs.filter((r) => r > 0).length / n) * 100 : 0, mean, sd };
}

export interface AiScore { ano: Group; ne: Group; t: number; earned: boolean; text: string }

export function aiScore(shadows: Shadow[]): AiScore {
  const done = shadows.filter((x) => x.ai && x.r != null);
  const ano = group(done.filter((x) => x.ai === "ano").map((x) => x.r!));
  const ne = group(done.filter((x) => x.ai === "ne").map((x) => x.r!));
  const se = Math.sqrt((ano.n > 1 ? ano.sd ** 2 / ano.n : 0) + (ne.n > 1 ? ne.sd ** 2 / ne.n : 0));
  const t = se > 0 ? (ano.mean - ne.mean) / se : 0;
  const earned = ano.n >= AI_MIN_N && ne.n >= AI_MIN_N && ne.mean < 0 && t >= AI_MIN_T;
  const text = earned
    ? `AI si právo veta vysloužilo: signály s jeho NE vychází ⌀ ${ne.mean.toFixed(2)} R, s ANO ⌀ ${ano.mean.toFixed(2)} R (t ${t.toFixed(1)}).`
    : ano.n < AI_MIN_N || ne.n < AI_MIN_N
      ? `Zatím jen radí – sbírám vyhodnocené signály (ANO ${ano.n}/${AI_MIN_N}, NE ${ne.n}/${AI_MIN_N}).`
      : `Zatím jen radí – jeho NE nepředpovídá horší výsledek dost jasně (NE ⌀ ${ne.mean.toFixed(2)} R, ANO ⌀ ${ano.mean.toFixed(2)} R, t ${t.toFixed(1)}).`;
  return { ano, ne, t, earned, text };
}
