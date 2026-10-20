import Link from 'next/link';
import { getUser } from '@/lib/supabase';
import { signOut } from '@/lib/actions';
import { AuthForm, RecoveryBridge, SubmitButton } from '@/components/forms';
import { Notice, PageHeading } from '@/components/ui';
export const metadata={title:'Conta'};
export default async function Account({searchParams}:{searchParams:Promise<{modo?:string;erro?:string}>}) {
  const params=await searchParams,user=await getUser();
  const mode=params.modo==='cadastro'?'cadastro':params.modo==='recuperar'?'recuperar':params.modo==='redefinir'?'redefinir':'entrar';
  if(user && mode!=='redefinir') return <><PageHeading title="Minha conta"><p>{user.email}</p></PageHeading><div className="account-summary"><p>Suas partidas e campos salvos estão vinculados a esta conta.</p><div className="inline-actions"><Link className="button primary" href="/partidas">Ver minhas partidas</Link><Link className="text-link" href="/conta?modo=redefinir">Alterar senha</Link></div><form action={signOut}><SubmitButton className="button">Sair da conta</SubmitButton></form></div></>;
  return <div className="account-layout"><section><p className="eyebrow">SUA CONTA</p><h1>{mode==='cadastro'?'Comece seu registro.':mode==='redefinir'?'Uma nova senha.':mode==='recuperar'?'Recupere o acesso.':'Bem-vindo de volta.'}</h1><p className="page-intro">Acesse suas partidas e os campos que você já cadastrou. O site pode ser visitado sem fazer login.</p><Link className="text-link" href="/">Voltar ao início</Link></section><section className="account-panel" aria-label="Acesso à conta">
    {params.erro && <Notice error>O link expirou ou não pôde ser verificado. Solicite outro email.</Notice>}
    <nav className="account-tabs" aria-label="Opções de acesso"><Link href="/conta" aria-current={mode==='entrar'?'page':undefined}>Entrar</Link><Link href="/conta?modo=cadastro" aria-current={mode==='cadastro'?'page':undefined}>Criar conta</Link></nav>
    {mode==='redefinir' && <RecoveryBridge />}
    {mode==='redefinir' && !user ? <><p>Abra o link enviado ao seu email para verificar o acesso antes de definir a senha.</p><Link className="text-link" href="/conta?modo=recuperar">Solicitar outro link</Link></> : <AuthForm key={mode} mode={mode} />}
    {mode!=='recuperar' && <Link className="help-link" href="/conta?modo=recuperar">Esqueci minha senha ou preciso confirmar o email</Link>}
  </section></div>;
}
