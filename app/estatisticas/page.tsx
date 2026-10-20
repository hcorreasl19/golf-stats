import { getUser } from '@/lib/supabase';
import { readRounds } from '@/lib/data';
import { aggregate, filterRounds, holeAnalysis, parseDate, pct, signed, statistics, type Filters } from '@/lib/golf';
import { Empty, FilterForm, GuestPrompt, Metrics, Notice, PageHeading } from '@/components/ui';
import { Trend, trends } from '@/components/trend';
export const metadata={title:'Estatísticas'};
export default async function Stats({searchParams}:{searchParams:Promise<Filters & {trend?:string;layout?:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Estatísticas" />;
  const params=await searchParams;
  let all;
  try {all=await readRounds();} catch {return <><PageHeading title="Estatísticas" /><Notice error>Não foi possível carregar as estatísticas. Tente atualizar a página.</Notice></>;}
  const lengths=[...new Set(all.rounds.map(r=>r.pars.length))].sort((a,b)=>a-b);
  const filters={...params,length:lengths.includes(Number(params.length))?params.length:String(lengths.at(-1)??18)};
  let rows;
  try {rows=filterRounds(all.rounds,filters);} catch(e) {return <><PageHeading title="Estatísticas" /><FilterForm rounds={all.rounds} filters={filters} stats /><Notice error>{(e as Error).message}</Notice></>;}
  const trend=params.trend&&params.trend in trends?params.trend:'score';
  const a=aggregate(rows),stats=rows.map(statistics);
  const layouts=[...new Set(rows.map(r=>JSON.stringify([r.course,r.pars])))];
  const chosen=layouts.includes(params.layout??'')?params.layout!:layouts[0];
  const holes=holeAnalysis(rows.filter(r=>JSON.stringify([r.course,r.pars])===chosen));
  const invalidDates=rows.filter(r=>!parseDate(r.date)).length;
  const categories=[['Albatross ou melhor','albatross'],['Eagles','eagles'],['Birdies','birdies'],['Pars','pars'],['Bogeys','bogeys'],['Double bogeys','doubles'],['Triple bogey ou pior','triples']] as const;
  return <><PageHeading title="Estatísticas" label="SEUS RESULTADOS"><p>Compare partidas da mesma quantidade de buracos. Os percentuais consideram o total de oportunidades registradas.</p></PageHeading>
    {all.skipped>0&&<Notice>{all.skipped} registro(s) incompleto(s) foram omitidos, sem apagar os dados originais.</Notice>}
    {all.rounds.length>0&&<FilterForm rounds={all.rounds} filters={filters} stats trend={trend} />}
    {!rows.length?<Empty>Ainda não há partidas para esta seleção.</Empty>:<>
      <Metrics items={[{label:'Partidas',value:a.count},{label:'Score médio',value:a.score!.toFixed(1)},{label:'Média ao par',value:signed(Number(a.toPar!.toFixed(1)))},{label:'Putts por partida',value:a.putts!.toFixed(1)}]} />
      <Metrics items={[{label:'GIR',value:pct(a.gir)},{label:'Fairways',value:pct(a.fairways)},{label:'Up-and-down',value:pct(a.upDown)}]} />
      <section className="report-section"><div className="section-line"><h2>Evolução · {trends[trend]}</h2></div>{invalidDates>0&&<Notice>{invalidDates} data(s) antiga(s) inválida(s) não aparecem no gráfico. Corrija-as editando a partida.</Notice>}<Trend rounds={rows} metric={trend} /></section>
      <div className="report-columns"><section><div className="section-line"><h2>Resultados por buraco</h2></div><table><thead><tr><th>Resultado</th><th>Quantidade</th></tr></thead><tbody>{categories.map(([label,key])=><tr key={key}><th scope="row">{label}</th><td>{stats.reduce((n,s)=>n+s[key],0)}</td></tr>)}</tbody></table></section>
      <section><div className="section-line"><h2>Médias e recordes</h2></div><dl className="record-list">{[{label:'Par 3',value:a.par3?.toFixed(2)??'Sem dados'},{label:'Par 4',value:a.par4?.toFixed(2)??'Sem dados'},{label:'Par 5',value:a.par5?.toFixed(2)??'Sem dados'},
        {label:'Melhor score',value:Math.min(...stats.map(s=>s.score))},{label:'Melhor ao par',value:signed(Math.min(...stats.map(s=>s.toPar)))},{label:'Menos putts',value:Math.min(...stats.map(s=>s.putts))}].map(v=><div key={v.label}><dt>{v.label}</dt><dd>{v.value}</dd></div>)}</dl><p className="hint">Recordes seguem os filtros acima. Campos e tees com ratings diferentes não são diretamente equivalentes.</p></section></div>
      <section className="report-section"><div className="section-line"><h2>Por campo e tee</h2></div><div className="table-scroll"><table><thead><tr><th>Campo</th><th>Par</th><th>Partidas</th><th>Score médio</th><th>GIR</th><th>Fairways</th></tr></thead><tbody>{layouts.map(key=>{
        const group=rows.filter(r=>JSON.stringify([r.course,r.pars])===key),s=aggregate(group);
        return <tr key={key}><th scope="row">{group[0].course}</th><td>{statistics(group[0]).par}</td><td>{s.count}</td><td>{s.score!.toFixed(1)}</td><td>{pct(s.gir)}</td><td>{pct(s.fairways)}</td></tr>;
      })}</tbody></table></div></section>
      <section className="report-section"><div className="section-line"><h2>Análise dos buracos</h2></div><form method="get" className="inline-filter">{Object.entries({...filters,trend}).filter(([k,v])=>k!=='layout'&&v).map(([k,v])=><input key={k} type="hidden" name={k} value={v} />)}<label>Campo, tee e scorecard<select name="layout" defaultValue={chosen}>{layouts.map((key,i)=>{const [course,pars]=JSON.parse(key) as [string,number[]];return <option value={key} key={key}>{course} · Par {pars.reduce((n,p)=>n+p,0)} · modelo {i+1}</option>;})}</select></label><button className="button" type="submit">Ver buracos</button></form>
      <div className="table-scroll"><table><thead><tr><th>Buraco</th><th>Par</th><th>Score médio</th><th>Ao par</th><th>Putts</th><th>GIR</th></tr></thead><tbody>{holes.map(h=><tr key={h.hole}><th scope="row">{h.hole}</th><td>{h.par}</td><td>{h.score.toFixed(2)}</td><td>{signed(Number(h.toPar.toFixed(2)))}</td><td>{h.putts.toFixed(2)}</td><td>{pct(h.gir)}</td></tr>)}</tbody></table></div><p className="hint">A comparação usa apenas partidas do mesmo campo, tee e sequência de pares.</p></section>
      <p className="hint">O handicap é informado manualmente. O site não calcula um índice oficial WHS.</p>
    </>}
  </>;
}
