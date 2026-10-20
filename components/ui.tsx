import Link from 'next/link';
import { dateLabel, pct, signed, statistics, type Filters, type Round } from '@/lib/golf';
export function PageHeading({ label, title, children, actions }: { label?: string; title: string; children?: React.ReactNode; actions?: React.ReactNode }) {
  return <header className="page-heading">{label && <p className="eyebrow">{label}</p>}<div className="heading-row"><h1>{title}</h1>{actions && <div className="heading-actions">{actions}</div>}</div>{children && <div className="page-intro">{children}</div>}</header>;
}
export function GuestPrompt({ title }: { title: string }) {
  return <><PageHeading title={title}><p>Entre para acessar seus registros. A conta reúne suas partidas, os campos salvos e as estatísticas.</p></PageHeading><div className="inline-actions"><Link className="button primary" href="/conta">Entrar</Link><Link className="text-link" href="/conta?modo=cadastro">Criar uma conta</Link></div></>;
}
export function Notice({ children, error = false }: { children: React.ReactNode; error?: boolean }) {
  return <p className={`notice ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}>{children}</p>;
}
export function Empty({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return <section className="empty"><p>{children}</p>{action}</section>;
}
export function Metrics({ items }: { items: { label: string; value: React.ReactNode; note?: string }[] }) {
  return <dl className="metrics">{items.map(item => <div key={item.label}><dt>{item.label}</dt><dd>{item.value}</dd>{item.note && <p>{item.note}</p>}</div>)}</dl>;
}
export function RoundTable({ rounds }: { rounds: Round[] }) {
  return <div className="table-scroll"><table><caption className="sr-only">Partidas ordenadas pela data em que foram jogadas</caption><thead><tr><th>Data</th><th>Campo / tee</th><th>Buracos</th><th>Score</th><th>Ao par</th><th>Putts</th><th>GIR</th><th>Fairways</th><th><span className="sr-only">Detalhes</span></th></tr></thead><tbody>{[...rounds].reverse().map(r => { const s=statistics(r); return <tr key={r.id}><td>{dateLabel(r.date)}</td><th scope="row"><Link href={`/partidas/${encodeURIComponent(r.id)}`}>{r.course}</Link></th><td>{s.holes}</td><td>{s.score}</td><td>{signed(s.toPar)}</td><td>{s.putts}</td><td>{pct(s.gir)}</td><td>{pct(s.fairways)}</td><td><Link className="table-link" href={`/partidas/${encodeURIComponent(r.id)}`} aria-label={`Ver partida de ${r.course} em ${dateLabel(r.date)}`}>Ver partida</Link></td></tr>; })}</tbody></table></div>;
}
export function FilterForm({ rounds, filters, stats = false, trend = 'score' }: { rounds: Round[]; filters: Filters; stats?: boolean; trend?: string }) {
  return <form method="get" className="filters"><div className="filter-fields"><label>Campo e tee<select aria-label="Campo e tee" name="course" defaultValue={filters.course ?? ''}><option value="">Todos os campos</option>{[...new Set(rounds.map(r=>r.course))].sort().map(c=><option key={c}>{c}</option>)}</select></label>
    <label>Buracos<select aria-label="Buracos" name="length" defaultValue={filters.length ?? ''}>{!stats && <option value="">9 e 18 buracos</option>}{[...new Set(rounds.map(r=>r.pars.length))].sort((a,b)=>a-b).map(n=><option key={n} value={n}>{n} buracos</option>)}</select></label>
    <label>De<input type="date" name="from" defaultValue={filters.from} /></label><label>Até<input type="date" name="to" defaultValue={filters.to} /></label>
    {!stats && <label>Buscar<input name="q" type="search" defaultValue={filters.q} placeholder="Campo, data ou score" /></label>}
    {stats && <label>Evolução<select aria-label="Evolução" name="trend" defaultValue={trend}>{[['score','Score'],['toPar','Ao par'],['putts','Putts'],['gir','GIR'],['fairways','Fairways'],['handicap','Handicap informado'],['penalties','Penalidades']].map(([key,label])=><option value={key} key={key}>{label}</option>)}</select></label>}
    <button type="submit" className="button">Aplicar filtros</button></div></form>;
}
