import Link from 'next/link';
import { getUser } from '@/lib/supabase';
import { readRounds } from '@/lib/data';
import { filterRounds, type Filters } from '@/lib/golf';
import { Empty, FilterForm, GuestPrompt, Notice, PageHeading, RoundTable } from '@/components/ui';
export const metadata={title:'Partidas'};
export default async function Rounds({searchParams}:{searchParams:Promise<Filters & {excluida?:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Suas partidas" />;
  const params=await searchParams;
  let loaded;
  try { loaded=await readRounds(); } catch { return <><PageHeading title="Partidas" /><Notice error>Não foi possível carregar suas partidas. Tente atualizar a página.</Notice></>; }
  const {rounds,skipped}=loaded;
  let rows;
  try { rows=filterRounds(rounds,params); } catch(e) { return <><PageHeading title="Partidas" /><FilterForm rounds={rounds} filters={params} /><Notice error>{(e as Error).message}</Notice></>; }
  return <><PageHeading title="Partidas" label="SEU HISTÓRICO" actions={<Link className="button primary" href="/partidas/nova">Registrar partida</Link>}><p>Consulte seus scorecards e corrija os registros quando precisar.</p></PageHeading>
    {params.excluida && <Notice>Partida excluída.</Notice>}{skipped>0 && <Notice>{skipped} registro(s) incompleto(s) foram omitidos. Os dados originais não foram apagados.</Notice>}
    {rounds.length>0 && <FilterForm rounds={rounds} filters={params} />}
    {rows.length ? <><p className="result-count">{rows.length} partida(s)</p><RoundTable rounds={rows} /></> : <Empty action={<Link className="text-link" href={rounds.length?'/partidas':'/partidas/nova'}>{rounds.length?'Limpar filtros':'Registrar minha primeira partida'}</Link>}>{rounds.length?'Nenhuma partida corresponde aos filtros.':'Você ainda não registrou nenhuma partida.'}</Empty>}
  </>;
}
