import 'server-only';
import { supabase, getUser } from './supabase';
import { chronological, COURSE_FIELD, layoutKey, savedLayouts, templates, usableRound, validLayout, validateRound, type Layout, type Round, type RoundInput } from './golf';
import { cache } from 'react';

export async function requireUser() {
  const user = await getUser();
  if (!user) throw new Error('Entre na sua conta para continuar.');
  return user;
}
export const readRounds = cache(async () => {
  const user = await requireUser(), db = await supabase();
  const rows: Round[] = []; let skipped = 0;
  for (let offset = 0; ; offset += 500) {
    const { data, error } = await db.from('rounds').select('*').eq('user_id', user.id).order('id').range(offset, offset + 499);
    if (error || !Array.isArray(data)) throw new Error('Não foi possível carregar suas partidas. Tente novamente.');
    for (const row of data) if (usableRound(row)) rows.push(row); else skipped++;
    if (data.length < 500) break;
  }
  return { rounds: chronological(rows), skipped };
});
export async function readRound(id: string) {
  const user = await requireUser(), db = await supabase();
  const { data, error } = await db.from('rounds').select('*').eq('id', id).eq('user_id', user.id).maybeSingle();
  if (error) throw new Error('Não foi possível carregar esta partida.');
  return usableRound(data) ? data : null;
}
export async function layouts() {
  const user = await requireUser();
  const { rounds } = await readRounds();
  return templates(rounds, savedLayouts(user.user_metadata));
}
export async function saveLayout(layout: Layout) {
  if (!validLayout(layout)) throw new Error('Preencha o campo e os pares de todos os buracos.');
  const user = await requireUser(), db = await supabase();
  const current = savedLayouts(user.user_metadata).filter(v => layoutKey(v) !== layoutKey(layout));
  current.push({ course: layout.course, pars: [...layout.pars] });
  const { error, data } = await db.auth.updateUser({ data: { [COURSE_FIELD]: current } });
  if (error || !data.user || !savedLayouts(data.user.user_metadata).some(v => layoutKey(v) === layoutKey(layout) && JSON.stringify(v.pars) === JSON.stringify(layout.pars))) throw new Error('Não foi possível confirmar o salvamento do campo.');
}
export async function saveRound(input: RoundInput, id?: string) {
  validateRound(input);
  const user = await requireUser(), db = await supabase();
  const query = id
    ? db.from('rounds').update(input).eq('id', id).eq('user_id', user.id)
    : db.from('rounds').insert({ ...input, user_id: user.id });
  const { data, error } = await query.select('id').single();
  if (error || !data) throw new Error('Não foi possível confirmar o salvamento. Confira o histórico antes de tentar novamente.');
  let layoutSaved = true;
  try { await saveLayout({ course: input.course, pars: input.pars }); } catch { layoutSaved = false; }
  return { id: String(data.id), layoutSaved };
}
export async function deleteRound(id: string) {
  const user = await requireUser(), db = await supabase();
  const { error, data } = await db.from('rounds').delete().eq('id', id).eq('user_id', user.id).select('id').single();
  if (error || !data) throw new Error('A exclusão não foi confirmada. Atualize o histórico e tente novamente.');
}
