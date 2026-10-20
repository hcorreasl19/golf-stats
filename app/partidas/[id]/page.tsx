import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getUser } from '@/lib/supabase';
import { readRound } from '@/lib/data';
import { dateLabel, pct, signed, statistics, sum } from '@/lib/golf';
import { DeleteForm } from '@/components/forms';
import { GuestPrompt, Metrics, Notice, PageHeading } from '@/components/ui';
export default async function RoundDetail({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{salva?:string;campo?:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Detalhes da partida" />;
  const {id}=await params,query=await searchParams;
  let round;
  try { round=await readRound(id); } catch { return <Notice error>Não foi possível carregar a partida. Atualize a página para tentar novamente.</Notice>; }
  if(!round) notFound();
  const s=statistics(round);
  return <><Link className="back-link" href="/partidas">Todas as partidas</Link><PageHeading title={round.course} label={dateLabel(round.date)} actions={<Link className="button" href={`/partidas/${encodeURIComponent(id)}/editar`}>Editar partida</Link>}><p>{s.holes} buracos · Par {s.par} · Handicap informado: {round.handicap}</p></PageHeading>
    {query.salva && <Notice>Partida salva.</Notice>}{query.campo==='pendente' && <Notice>O scorecard foi salvo, mas o campo não pôde ser sincronizado separadamente. Abra Campos e salve o modelo para mantê-lo independente do histórico.</Notice>}
    <Metrics items={[{label:'Score',value:s.score},{label:'Ao par',value:signed(s.toPar)},{label:'Putts',value:s.putts},{label:'GIR',value:pct(s.gir)}]} />
    <div className="section-line"><h2>Scorecard</h2></div><div className="table-scroll"><table><thead><tr><th>Buraco</th><th>Par</th><th>Score</th><th>Ao par</th><th>Putts</th><th>GIR</th><th>Penalidades</th></tr></thead><tbody>{round.pars.map((p,i)=><tr key={i}><th scope="row">{i+1}</th><td>{p}</td><td>{round.scores[i]}</td><td>{signed(round.scores[i]-p)}</td><td>{round.putts[i]}</td><td>{round.girs[i]?'Sim':'Não'}</td><td>{round.penalties[i]}</td></tr>)}</tbody><tfoot><tr><th>Total</th><td>{sum(round.pars)}</td><td>{s.score}</td><td>{signed(s.toPar)}</td><td>{s.putts}</td><td>{pct(s.gir)}</td><td>{s.penalties}</td></tr></tfoot></table></div>
    <Metrics items={[{label:'Fairways',value:pct(s.fairways),note:`${round.fairways_hit} acertos em ${round.fairway_opportunities} oportunidades`},{label:'Up-and-down',value:pct(s.upDown),note:`${round.up_and_downs_converted} conversões em ${round.up_and_down_opportunities} oportunidades`},{label:'Primeiros 9',value:s.front},{label:'Últimos 9',value:s.back??'Não se aplica'}]} />
    <details className="danger-section"><summary>Excluir esta partida</summary><p>A exclusão é definitiva. Confira o campo e a data acima.</p><DeleteForm id={id} /></details>
  </>;
}
