'use client';
export default function ErrorPage({reset}:{reset:()=>void}){return <section className="empty"><h1>Não foi possível carregar a página.</h1><p>Seus registros não foram alterados. Tente novamente em instantes.</p><button className="button" onClick={reset}>Tentar novamente</button></section>;}
