import Link from 'next/link';
export default function NotFound(){return <section className="empty"><h1>Registro não encontrado.</h1><p>Ele pode ter sido removido ou não pertencer à sua conta.</p><Link className="button" href="/partidas">Voltar às partidas</Link></section>;}
