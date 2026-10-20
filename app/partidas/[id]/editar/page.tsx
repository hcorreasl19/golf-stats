import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getUser } from '@/lib/supabase';
import { readRound } from '@/lib/data';
import { RoundEditor } from '@/components/forms';
import { GuestPrompt, Notice, PageHeading } from '@/components/ui';
export const metadata={title:'Editar partida'};
export default async function EditRound({params}:{params:Promise<{id:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Editar partida" />;
  const {id}=await params;
  let round;
  try {round=await readRound(id);} catch {return <Notice error>Não foi possível carregar a partida.</Notice>;}
  if(!round) notFound();
  return <><Link className="back-link" href={`/partidas/${encodeURIComponent(id)}`}>Voltar à partida</Link><PageHeading title="Editar partida"><p>Apenas este registro será alterado. As outras partidas manterão seus scorecards originais.</p></PageHeading><RoundEditor choices={[]} initial={round} /></>;
}
