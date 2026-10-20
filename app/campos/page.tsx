import Link from 'next/link';
import { getUser } from '@/lib/supabase';
import { layouts } from '@/lib/data';
import { layoutKey, sum } from '@/lib/golf';
import { CourseEditor } from '@/components/forms';
import { GuestPrompt, Notice, PageHeading } from '@/components/ui';
export const metadata={title:'Campos salvos'};
export default async function Courses({searchParams}:{searchParams:Promise<{editar?:string;salvo?:string}>}) {
  if(!await getUser()) return <GuestPrompt title="Campos salvos" />;
  const params=await searchParams;
  let choices;
  try {choices=await layouts();} catch {return <><PageHeading title="Campos salvos" /><Notice error>Não foi possível carregar seus campos. Tente atualizar a página.</Notice></>;}
  const initial=choices.find(c=>layoutKey(c)===params.editar);
  return <><PageHeading title="Campos salvos" label="SUA BIBLIOTECA"><p>Cadastre o campo e os pares uma vez. Depois, selecione o mesmo percurso ao registrar uma partida.</p></PageHeading>{params.salvo&&<Notice>Campo salvo na sua conta.</Notice>}
    {choices.length>0?<div className="course-list">{choices.map(c=><section className="course-row" key={layoutKey(c)}><div><h2>{c.course}</h2><p>{c.pars.length} buracos · Par {sum(c.pars)}</p><div className="par-strip" aria-label="Pares dos buracos">{c.pars.map((p,i)=><span key={i}><small>{i+1}</small><strong>{p}</strong></span>)}</div></div><div className="course-actions"><Link className="button primary" href={`/partidas/nova?campo=${encodeURIComponent(layoutKey(c))}`}>Jogar neste campo</Link><Link className="text-link" href={`/campos?editar=${encodeURIComponent(layoutKey(c))}#cadastro`}>Editar pares</Link></div></section>)}</div>:<p className="empty">Você ainda não salvou nenhum campo. Comece pelo formulário abaixo ou registre sua primeira partida.</p>}
    <section id="cadastro" className="course-editor"><div className="section-line"><h2>{initial?'Atualizar campo':'Cadastrar campo'}</h2>{initial&&<Link className="text-link" href="/campos#cadastro">Cadastrar outro</Link>}</div><CourseEditor key={initial?layoutKey(initial):'new'} initial={initial} /></section>
  </>;
}
