'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
export function Navigation() {
  const path = usePathname();
  return <nav aria-label="Navegação principal">{[['/partidas','Partidas'],['/campos','Campos'],['/estatisticas','Estatísticas']].map(([href,label]) => <Link key={href} href={href} aria-current={path.startsWith(href) ? 'page' : undefined}>{label}</Link>)}</nav>;
}
