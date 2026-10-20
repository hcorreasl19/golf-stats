import Link from 'next/link';
import { getUser } from '@/lib/supabase';
export default async function Home() {
  const user=await getUser();
  return <>
    <section className="home-hero"><p className="eyebrow">SEU HISTÓRICO DE JOGO</p><h1>Seu histórico<br />de golfe.</h1><div className="hero-bottom"><p>Registre o scorecard de 9 ou 18 buracos. Os pares dos campos ficam salvos para a próxima partida.</p><div className="inline-actions"><Link className="button primary" href="/partidas/nova">Registrar uma partida</Link>{!user && <Link className="text-link" href="/conta?modo=cadastro">Criar conta</Link>}</div></div></section>
    <section className="home-index" aria-labelledby="index-title"><div><p className="eyebrow">NO SEU REGISTRO</p><h2 id="index-title">Consulte seus<br />registros.</h2><p className="muted">Seus dados ficam associados à sua conta. Você pode voltar para corrigir uma partida ou consultar o que já jogou.</p></div><div className="index-links">
      <Link href="/partidas"><span><strong>Partidas</strong><small>Scorecards, datas e resultados. Edite quando precisar.</small></span><span className="link-arrow" aria-hidden="true" /></Link>
      <Link href="/campos"><span><strong>Campos salvos</strong><small>Cadastre os pares uma vez. Reutilize nas próximas partidas.</small></span><span className="link-arrow" aria-hidden="true" /></Link>
      <Link href="/estatisticas"><span><strong>Estatísticas</strong><small>Consulte seus scores, putts, fairways e greens.</small></span><span className="link-arrow" aria-hidden="true" /></Link>
    </div></section>
  </>;
}
