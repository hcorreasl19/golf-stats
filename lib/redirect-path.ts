/** Only relative destinations on this application may be used after auth. */
export function safeNext(value: string | null) {
  if (!value || !value.startsWith('/') || value.startsWith('//') || /[\u0000-\u0020\\]/.test(value)) return '/partidas';
  const base='https://golf-stats.invalid';
  try { const url=new URL(value,base); return url.origin===base ? url.pathname+url.search+url.hash : '/partidas'; } catch { return '/partidas'; }
}
