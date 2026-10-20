import { getUser } from '@/lib/supabase';
import { layouts } from '@/lib/data';
import { RoundEditor } from '@/components/forms';
import { GuestPrompt, Notice, PageHeading } from '@/components/ui';
export const metadata={title:'Registrar partida'};
export default async function NewRound({searchParams}:{searchParams:Promise<{campo?:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Registrar partida" />;
  const params=await searchParams;
  let choices;
  try { choices=await layouts(); } catch { return <><PageHeading title="Registrar partida" /><Notice error>Não foi possível carregar seus campos. Atualize a página antes de continuar.</Notice></>; }
  return <><PageHeading title="Registrar partida" label="NOVO SCORECARD"><p>Selecione um campo salvo para preencher os pares automaticamente ou cadastre um novo.</p></PageHeading><RoundEditor choices={choices} preset={params.campo} /></>;
}
