'use server';
import { headers, cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { revalidatePath } from 'next/cache';
import { supabase, getUser, config } from './supabase';
import { saveRound, deleteRound, saveLayout } from './data';
import { courseName, type RoundInput } from './golf';

export type FormState = { error?: string; success?: string };
const text = (form: FormData, key: string) => String(form.get(key) ?? '').trim();
const number = (form: FormData, key: string) => text(form, key) === '' ? NaN : Number(text(form, key));
function email(form: FormData) {
  const value = text(form, 'email');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) throw new Error('Informe um email válido.');
  return value;
}
function password(form: FormData) {
  const value = String(form.get('password') ?? '');
  if (value.length < 8) throw new Error('Use uma senha com pelo menos 8 caracteres.');
  if (value !== form.get('confirmation')) throw new Error('As senhas não coincidem.');
  return value;
}
const message = (e: unknown, fallback: string) => e instanceof Error && !('status' in e) && !('code' in e) ? e.message : fallback;
async function origin() {
  const h = await headers();
  const value = h.get('origin');
  if (!value) throw new Error('Não foi possível verificar a origem da solicitação.');
  return new URL(value).origin;
}
export async function signIn(_: FormState, form: FormData): Promise<FormState> {
  try {
    const value = email(form), pass = String(form.get('password') ?? '');
    if (!pass) return { error: 'Informe sua senha.' };
    const db = await supabase();
    const { data, error } = await db.auth.signInWithPassword({ email: value, password: pass });
    if (error || !data.user || !data.session) return { error: 'Não foi possível entrar. Confira os dados e a confirmação do seu email.' };
  } catch { return { error: 'Não foi possível entrar. Confira os dados e tente novamente.' }; }
  redirect('/partidas');
}
export async function signUp(_: FormState, form: FormData): Promise<FormState> {
  let address: string, pass: string;
  try { address = email(form); pass = password(form); } catch (e) { return { error: message(e, 'Confira os dados.') }; }
  try {
    const db = await supabase();
    const { data, error } = await db.auth.signUp({ email: address, password: pass, options: { emailRedirectTo: `${await origin()}/auth/callback` } });
    if (error) return { error: 'Não foi possível criar a conta. Confira os requisitos da senha ou tente entrar se já possui cadastro.' };
    if (!data.session) return { success: 'Confira seu email para confirmar o cadastro. Depois, entre na sua conta.' };
  } catch { return { error: 'Não foi possível concluir o cadastro. Tente novamente.' }; }
  redirect('/partidas');
}
export async function signOut() {
  try {
    const db = await supabase();
    const { error } = await db.auth.signOut();
    if (error) await db.auth.signOut({ scope: 'local' });
  } catch { /* Local logout still completes when Supabase is unavailable. */ }
  const value = config();
  if (value) {
    const prefix = `sb-${new URL(value.url).hostname.split('.')[0]}-auth-token`;
    const store = await cookies();
    for (const cookie of store.getAll()) if (cookie.name.startsWith(prefix)) store.delete(cookie.name);
  }
  revalidatePath('/', 'layout');
  redirect('/');
}

export async function sendAccountEmail(_: FormState, form: FormData): Promise<FormState> {
  let address: string;
  try { address = email(form); } catch (e) { return { error: message(e, 'Confira o email.') }; }
  try {
    const db = await supabase();
    const callback = `${await origin()}/auth/callback`;
    const { error } = text(form, 'kind') === 'confirmation'
      ? await db.auth.resend({ type: 'signup', email: address, options: { emailRedirectTo: callback } })
      : await db.auth.resetPasswordForEmail(address, { redirectTo: `${callback}?next=${encodeURIComponent('/conta?modo=redefinir')}` });
    if (error) return { error: 'Não foi possível enviar o email agora. Tente novamente em alguns minutos.' };
    return { success: 'Se a conta estiver apta, o email chegará em instantes. Confira também a pasta de spam.' };
  } catch { return { error: 'Não foi possível solicitar o email. Tente novamente.' }; }
}
export async function changePassword(_: FormState, form: FormData): Promise<FormState> {
  let value: string;
  try { value = password(form); } catch (e) { return { error: message(e, 'Confira a nova senha.') }; }
  try {
    if (!await getUser()) return { error: 'Abra um link de recuperação válido antes de alterar a senha.' };
    const db = await supabase();
    const { error } = await db.auth.updateUser({ password: value });
    if (error) return { error: 'Não foi possível alterar a senha. Solicite um novo link e tente novamente.' };
    return { success: 'Senha atualizada. Você já pode usar a nova senha.' };
  } catch { return { error: 'Não foi possível atualizar a senha.' }; }
}
export async function establishRecovery(accessToken: string, refreshToken: string): Promise<FormState> {
  try {
    if (!accessToken || !refreshToken || accessToken.length > 20000 || refreshToken.length > 20000) return { error: 'Link inválido.' };
    const db = await supabase();
    const { data, error } = await db.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
    if (error || !data.user || !data.session) return { error: 'O link expirou ou já foi utilizado. Solicite outro email.' };
    revalidatePath('/conta');
    return { success: 'Link verificado.' };
  } catch { return { error: 'Não foi possível verificar o link de recuperação.' }; }
}
export async function saveRoundAction(_: FormState, form: FormData): Promise<FormState> {
  let id = '', layoutSaved = false;
  try {
    const n = number(form, 'holes');
    if (![9, 18].includes(n)) throw new Error('Escolha 9 ou 18 buracos.');
    const values = (name: string) => Array.from({ length: n }, (_, i) => number(form, `${name}_${i}`));
    const input: RoundInput = { course: courseName(text(form, 'course'), text(form, 'tee')), date: text(form, 'date'), handicap: number(form, 'handicap'),
      pars: values('par'), scores: values('score'), putts: values('putts'), penalties: values('penalty'),
      girs: Array.from({ length: n }, (_, i) => form.get(`gir_${i}`) === 'on' ? 1 : 0),
      fairway_opportunities: number(form, 'fairway_opportunities'), fairways_hit: number(form, 'fairways_hit'),
      up_and_down_opportunities: number(form, 'up_and_down_opportunities'), up_and_downs_converted: number(form, 'up_and_downs_converted') };
    ({ id, layoutSaved } = await saveRound(input, text(form, 'id') || undefined));
  } catch (e) { return { error: message(e, 'O salvamento não foi confirmado. Confira o histórico antes de tentar novamente.') }; }
  revalidatePath('/partidas'); revalidatePath(`/partidas/${encodeURIComponent(id)}`); revalidatePath('/campos'); revalidatePath('/estatisticas');
  redirect(`/partidas/${encodeURIComponent(id)}?salva=1${layoutSaved ? '' : '&campo=pendente'}`);
}
export async function deleteRoundAction(_: FormState, form: FormData): Promise<FormState> {
  if (form.get('confirm') !== 'yes') return { error: 'Confirme a exclusão antes de continuar.' };
  const id = text(form, 'id');
  try { await deleteRound(id); } catch { return { error: 'A exclusão não foi confirmada. Atualize o histórico antes de tentar novamente.' }; }
  revalidatePath('/partidas'); revalidatePath(`/partidas/${encodeURIComponent(id)}`); revalidatePath('/estatisticas');
  redirect('/partidas?excluida=1');
}
export async function saveCourseAction(_: FormState, form: FormData): Promise<FormState> {
  try {
    const n = number(form, 'holes');
    if (![9, 18].includes(n)) throw new Error('Escolha 9 ou 18 buracos.');
    await saveLayout({ course: courseName(text(form, 'course'), text(form, 'tee')), pars: Array.from({ length: n }, (_, i) => number(form, `par_${i}`)) });
  } catch (e) { return { error: message(e, 'Não foi possível salvar o campo. Tente novamente.') }; }
  revalidatePath('/campos'); revalidatePath('/partidas/nova');
  redirect('/campos?salvo=1');
}
