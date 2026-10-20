import type { Metadata } from 'next';
import Link from 'next/link';
import { getUser } from '@/lib/supabase';
import { Navigation } from '@/components/navigation';
import './globals.css';
export const metadata: Metadata = { title: { default: 'Golf Stats', template: '%s · Golf Stats' }, description: 'Registre suas partidas de golfe, salve os campos e acompanhe suas estatísticas.' };
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const user=await getUser();
  return <html lang="pt-BR" data-scroll-behavior="smooth"><body><a className="skip-link" href="#conteudo">Pular para o conteúdo</a><div className="site-shell"><header className="site-header"><Link className="wordmark" href="/" aria-label="Golf Stats — início">golf<span>stats</span><small>REGISTRO DE GOLFE</small></Link><Navigation /><Link className="button account-link" href="/conta">{user ? 'Minha conta' : 'Entrar'}</Link></header><main id="conteudo">{children}</main><footer className="site-footer"><Link href="/">Golf Stats</Link><span>Partidas de 9 e 18 buracos.</span><Link href="/campos">Seus campos salvos</Link></footer></div></body></html>;
}
