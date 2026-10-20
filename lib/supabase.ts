import 'server-only';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { cache } from 'react';

export function config() {
  const raw = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!raw || !key) return null;
  const url = new URL(raw.replace(/\/rest\/v1\/?$/, '').replace(/\/$/, ''));
  if (url.protocol !== 'https:' && !(process.env.NODE_ENV !== 'production' && ['127.0.0.1', 'localhost'].includes(url.hostname))) throw new Error('Supabase requires HTTPS.');
  return { url: url.toString().replace(/\/$/, ''), key };
}
export async function supabase() {
  const value = config();
  if (!value) throw new Error('A conexão está temporariamente indisponível.');
  const store = await cookies();
  return createServerClient(value.url, value.key, {
    cookieOptions: { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/' },
    cookies: {
      getAll: () => store.getAll(),
      setAll: (all) => { try { for (const { name, value, options } of all) store.set(name, value, options); } catch { /* The proxy refreshes cookies for server-rendered pages. */ } },
    },
  });
}
export const getUser = cache(async () => {
  if (!config()) return null;
  const db = await supabase();
  const { data: { user } } = await db.auth.getUser();
  return user;
});
