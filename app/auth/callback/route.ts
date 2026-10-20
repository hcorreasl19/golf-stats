import { NextResponse, type NextRequest } from 'next/server';
import { supabase } from '@/lib/supabase';
import type { EmailOtpType } from '@supabase/supabase-js';
import { safeNext } from '@/lib/redirect-path';
export async function GET(request: NextRequest) {
  // Preserve the browser host when the runtime uses an internal localhost URL.
  const host = request.headers.get('host') ?? request.nextUrl.host;
  const protocol = process.env.NODE_ENV === 'production' || request.headers.get('x-forwarded-proto') === 'https' ? 'https:' : 'http:';
  const origin = `${protocol}//${host}`;
  const params = request.nextUrl.searchParams;
  const code = params.get('code'), tokenHash = params.get('token_hash'), kind = params.get('type');
  const target = kind === 'recovery' ? '/conta?modo=redefinir' : safeNext(params.get('next'));
  if (!code && !tokenHash) return NextResponse.redirect(new URL('/conta?modo=redefinir', origin));
  try {
    const db = await supabase();
    const result = code ? await db.auth.exchangeCodeForSession(code)
      : ['signup', 'recovery', 'email'].includes(kind ?? '') ? await db.auth.verifyOtp({ token_hash: tokenHash!, type: kind as EmailOtpType }) : { error: true };
    if (!result.error) return NextResponse.redirect(new URL(target, origin));
  } catch { /* Show a generic error without exposing the token. */ }
  return NextResponse.redirect(new URL('/conta?erro=link', origin));
}
