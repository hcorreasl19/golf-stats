import { dateLabel, parseDate, statistics, type Round } from '@/lib/golf';
export const trends: Record<string,string>={score:'Score',toPar:'Ao par',putts:'Putts',gir:'GIR (%)',fairways:'Fairways (%)',handicap:'Handicap informado',penalties:'Penalidades'};
export function Trend({rounds,metric}:{rounds:Round[];metric:string}) {
  const key=metric in trends?metric:'score';
  const points=rounds.filter(r=>parseDate(r.date)).map(r=>{
    const s=statistics(r);
    const value=key==='handicap'?r.handicap:s[key as keyof typeof s];
    return {date:parseDate(r.date)!,value:typeof value==='number'?value:null};
  });
  const values=points.flatMap(p=>p.value===null?[]:[p.value]);
  if(!values.length) return <p className="empty">Ainda não há dados para esta evolução.</p>;
  const width=1000,height=260,left=55,right=25,top=25,bottom=45;
  let min=Math.min(...values),max=Math.max(...values);
  if(min===max){min-=1;max+=1;}
  const dates=points.map(p=>Date.parse(`${p.date}T12:00:00Z`)),start=Math.min(...dates),end=Math.max(...dates);
  const x=(i:number)=>left+(end===start?.5:(dates[i]-start)/(end-start))*(width-left-right);
  const y=(v:number)=>top+(max-v)/(max-min)*(height-top-bottom);
  const segments:string[][]=[[]];
  points.forEach((p,i)=>{if(p.value===null){if(segments.at(-1)!.length)segments.push([]);}else segments.at(-1)!.push(`${x(i)},${y(p.value)}`);});
  return <div className="trend"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Evolução de ${trends[key]} por data da partida`}>
    <title>{trends[key]} por data da partida</title>
    {[min,(min+max)/2,max].map((v,i)=><g key={i}><line x1={left} x2={width-right} y1={y(v)} y2={y(v)} className="grid-line"/><text x={left-12} y={y(v)+4} textAnchor="end">{Number(v.toFixed(1))}</text></g>)}
    {segments.filter(s=>s.length>1).map((s,i)=><polyline key={i} points={s.join(' ')} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />)}
    {points.map((p,i)=>p.value!==null&&<circle key={i} cx={x(i)} cy={y(p.value)} r="4" fill="currentColor"><title>{dateLabel(p.date)}: {p.value.toFixed(1)}</title></circle>)}
    <text x={left} y={height-10}>{dateLabel(points[0].date)}</text>{points.at(-1)!.date!==points[0].date&&<text textAnchor="end" x={width-right} y={height-10}>{dateLabel(points.at(-1)!.date)}</text>}
  </svg><details><summary>Ver os valores do gráfico</summary><table><thead><tr><th>Data</th><th>{trends[key]}</th></tr></thead><tbody>{points.map((p,i)=><tr key={i}><td>{dateLabel(p.date)}</td><td>{p.value===null?'Sem dados':p.value.toFixed(1)}</td></tr>)}</tbody></table></details></div>;
}
