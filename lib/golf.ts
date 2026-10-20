export type Layout = { course: string; pars: number[] };
export type RoundInput = {
  course: string; date: string; handicap: number;
  pars: number[]; scores: number[]; putts: number[]; girs: number[]; penalties: number[];
  fairway_opportunities: number; fairways_hit: number;
  up_and_down_opportunities: number; up_and_downs_converted: number;
};
export type Round = RoundInput & { id: string | number };
export const COURSE_FIELD = 'golf_course_layouts_v1';
export function today() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}
export function parseDate(raw: string): string | null {
  let value = raw;
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) {
    const [d, m, y] = value.split('/'); value = `${y}-${m}-${d}`;
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const parsed = new Date(`${value}T12:00:00Z`);
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value ? value : null;
}
export function dateLabel(raw: string) {
  const parsed = parseDate(raw); return parsed ? parsed.split('-').reverse().join('/') : raw;
}
export function chronological(rounds: Round[]) {
  return [...rounds].sort((a, b) => (parseDate(a.date) ?? '').localeCompare(parseDate(b.date) ?? '') || String(a.id).localeCompare(String(b.id), undefined, { numeric: true }));
}
export function courseName(name: string, tee: string) {
  name = name.trim().replace(/\s+/g, ' '); tee = tee.trim().replace(/\s+/g, ' ');
  if (!name) throw new Error('Informe o nome do campo.');
  if (name.includes(' · Tee: ') || tee.includes(' · Tee: ')) throw new Error('Não use o separador reservado no nome.');
  return tee ? `${name} · Tee: ${tee}` : name;
}
export function splitCourse(label: string) {
  const at = label.lastIndexOf(' · Tee: ');
  return at < 0 ? { name: label, tee: '' } : { name: label.slice(0, at), tee: label.slice(at + 8) };
}
export function layoutKey(layout: Layout) { return JSON.stringify([layout.course.toLocaleLowerCase(), layout.pars.length]); }
export function validLayout(value: unknown): value is Layout {
  if (!value || typeof value !== 'object') return false;
  const v = value as Layout;
  return typeof v.course === 'string' && !!v.course.trim() && Array.isArray(v.pars) && [9, 18].includes(v.pars.length) && v.pars.every(p => Number.isInteger(p) && [3, 4, 5].includes(p));
}
export function savedLayouts(metadata: Record<string, unknown> | undefined): Layout[] {
  const raw = metadata?.[COURSE_FIELD];
  return Array.isArray(raw) ? raw.filter(validLayout) : [];
}
export function templates(rounds: Round[], saved: Layout[] = []) {
  const map = new Map<string, Layout>();
  for (const value of [...chronological(rounds), ...saved]) if (validLayout(value)) map.set(layoutKey(value), { course: value.course, pars: [...value.pars] });
  return [...map.values()].sort((a, b) => a.course.localeCompare(b.course));
}
export function validateRound(r: RoundInput, currentDate = today()) {
  if (!r.course.trim()) throw new Error('Informe o nome do campo.');
  const day = parseDate(r.date);
  if (!day || day > currentDate) throw new Error('Informe uma data válida, que não esteja no futuro.');
  const n = r.pars.length;
  if (![9, 18].includes(n)) throw new Error('A partida deve ter 9 ou 18 buracos.');
  for (const field of ['pars', 'scores', 'putts', 'girs', 'penalties'] as const) {
    if (!Array.isArray(r[field]) || r[field].length !== n || !r[field].every(Number.isInteger)) throw new Error('Preencha os dados de todos os buracos.');
  }
  for (let i = 0; i < n; i++) {
    if (![3, 4, 5].includes(r.pars[i]) || r.scores[i] < 1 || r.putts[i] < 0 || r.penalties[i] < 0 || ![0, 1].includes(r.girs[i])) throw new Error(`Confira os valores do buraco ${i + 1}.`);
    if (r.putts[i] + r.penalties[i] > r.scores[i]) throw new Error(`Buraco ${i + 1}: putts e penalidades não podem ultrapassar o score.`);
  }
  if (!Number.isFinite(r.handicap) || r.handicap < -10 || r.handicap > 54) throw new Error('Informe um handicap entre -10 e 54.');
  const counters = [r.fairway_opportunities, r.fairways_hit, r.up_and_down_opportunities, r.up_and_downs_converted];
  if (!counters.every(v => Number.isInteger(v) && v >= 0)) throw new Error('Informe contagens válidas de fairways e up-and-downs.');
  if (r.fairways_hit > r.fairway_opportunities || r.fairway_opportunities > r.pars.filter(p => p > 3).length) throw new Error('Fairways acertados não podem ultrapassar as oportunidades nos pares 4 e 5.');
  if (r.up_and_downs_converted > r.up_and_down_opportunities || r.up_and_down_opportunities > n - sum(r.girs)) throw new Error('Confira os up-and-downs e as oportunidades nos buracos sem GIR.');
  return r;
}
export const sum = (values: number[]) => values.reduce((a, b) => a + b, 0);
export const ratio = (hits: number, opportunities: number) => opportunities ? hits / opportunities * 100 : null;
export function statistics(r: RoundInput) {
  const diffs = r.scores.map((s, i) => s - r.pars[i]);
  return { holes: r.pars.length, score: sum(r.scores), par: sum(r.pars), toPar: sum(diffs), putts: sum(r.putts), penalties: sum(r.penalties),
    gir: ratio(sum(r.girs), r.pars.length), fairways: ratio(r.fairways_hit, r.fairway_opportunities), upDown: ratio(r.up_and_downs_converted, r.up_and_down_opportunities),
    albatross: diffs.filter(d => d <= -3).length, eagles: diffs.filter(d => d === -2).length, birdies: diffs.filter(d => d === -1).length,
    pars: diffs.filter(d => d === 0).length, bogeys: diffs.filter(d => d === 1).length, doubles: diffs.filter(d => d === 2).length, triples: diffs.filter(d => d >= 3).length,
    front: sum(r.scores.slice(0, 9)), back: r.pars.length === 18 ? sum(r.scores.slice(9)) : null };
}
export function aggregate(rounds: Round[]) {
  const count = rounds.length, stats = rounds.map(statistics);
  const parAverage = (par: number) => { const scores = rounds.flatMap(r => r.scores.filter((_, i) => r.pars[i] === par)); return scores.length ? sum(scores) / scores.length : null; };
  return { count, score: count ? sum(stats.map(s => s.score)) / count : null, putts: count ? sum(stats.map(s => s.putts)) / count : null,
    toPar: count ? sum(stats.map(s => s.toPar)) / count : null,
    gir: ratio(sum(rounds.map(r => sum(r.girs))), sum(rounds.map(r => r.pars.length))),
    fairways: ratio(sum(rounds.map(r => r.fairways_hit)), sum(rounds.map(r => r.fairway_opportunities))),
    upDown: ratio(sum(rounds.map(r => r.up_and_downs_converted)), sum(rounds.map(r => r.up_and_down_opportunities))),
    par3: parAverage(3), par4: parAverage(4), par5: parAverage(5) };
}
export function holeAnalysis(rounds: Round[]) {
  if (!rounds.length) return [];
  if (new Set(rounds.map(r => JSON.stringify([r.course, r.pars]))).size > 1) throw new Error('Selecione um único campo, tee e scorecard.');
  return rounds[0].pars.map((par, i) => ({ hole: i + 1, par, score: sum(rounds.map(r => r.scores[i])) / rounds.length,
    toPar: sum(rounds.map(r => r.scores[i] - r.pars[i])) / rounds.length,
    putts: sum(rounds.map(r => r.putts[i])) / rounds.length, gir: ratio(sum(rounds.map(r => r.girs[i])), rounds.length) }));
}
export function usableRound(value: unknown): value is Round {
  if (!value || typeof value !== 'object') return false;
  const r = value as Round;
  return (typeof r.id === 'string' || typeof r.id === 'number') && typeof r.course === 'string' && typeof r.date === 'string' && Number.isFinite(r.handicap) &&
    Array.isArray(r.pars) && [9, 18].includes(r.pars.length) && ['pars','scores','putts','girs','penalties'].every(k => {
      const v = r[k as keyof Round]; return Array.isArray(v) && v.length === r.pars.length && v.every(n => typeof n === 'number' && Number.isFinite(n));
    }) && [r.fairway_opportunities,r.fairways_hit,r.up_and_down_opportunities,r.up_and_downs_converted].every(Number.isFinite);
}
export type Filters = { course?: string; length?: string; from?: string; to?: string; q?: string };
export function filterRounds(rounds: Round[], filters: Filters) {
  if ((filters.from && !parseDate(filters.from)) || (filters.to && !parseDate(filters.to))) throw new Error('Use datas válidas nos filtros.');
  if (filters.from && filters.to && filters.from > filters.to) throw new Error('A data inicial deve vir antes da final.');
  return chronological(rounds).filter(r => {
    const day = parseDate(r.date);
    return (!filters.course || r.course === filters.course) && (!filters.length || r.pars.length === Number(filters.length)) &&
      (!filters.from || (!!day && day >= filters.from)) && (!filters.to || (!!day && day <= filters.to)) &&
      (!filters.q || `${r.course} ${r.date} ${dateLabel(r.date)} ${sum(r.scores)}`.toLocaleLowerCase().includes(filters.q.toLocaleLowerCase()));
  });
}
export const pct = (value: number | null) => value === null ? 'Sem dados' : `${value.toFixed(1)}%`;
export const signed = (value: number) => value === 0 ? 'E' : `${value > 0 ? '+' : ''}${value}`;
