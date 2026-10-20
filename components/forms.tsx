'use client';
import { useActionState, useEffect, useState, useTransition } from 'react';
import { useFormStatus } from 'react-dom';
import { useRouter } from 'next/navigation';
import { changePassword, deleteRoundAction, establishRecovery, saveCourseAction, saveRoundAction, sendAccountEmail, signIn, signUp, type FormState } from '@/lib/actions';
import { layoutKey, parseDate, splitCourse, sum, today, type Layout, type Round } from '@/lib/golf';

export function SubmitButton({ children, pendingText = 'Aguarde…', className = 'button primary' }: { children: React.ReactNode; pendingText?: string; className?: string }) {
  const { pending } = useFormStatus();
  return <button className={className} type="submit" disabled={pending}>{pending ? pendingText : children}</button>;
}
export function Feedback({ state }: { state: FormState }) {
  return <div aria-live="polite">{state.error && <p className="notice error" role="alert">{state.error}</p>}{state.success && <p className="notice success" role="status">{state.success}</p>}</div>;
}
export function AuthForm({ mode }: { mode: 'entrar' | 'cadastro' | 'recuperar' | 'redefinir' }) {
  const action = mode === 'entrar' ? signIn : mode === 'cadastro' ? signUp : mode === 'redefinir' ? changePassword : sendAccountEmail;
  const [state, dispatch] = useActionState(action, {} as FormState);
  const [address,setAddress]=useState(''),[kind,setKind]=useState('recovery');
  return <form action={dispatch} className="form-stack">
    <Feedback state={state} />
    {mode !== 'redefinir' && <label>Email<input name="email" type="email" autoComplete="email" value={address} onChange={e=>setAddress(e.target.value)} required /></label>}
    {(mode === 'entrar' || mode === 'cadastro' || mode === 'redefinir') && <label>{mode === 'redefinir' ? 'Nova senha' : 'Senha'}<input name="password" type="password" autoComplete={mode === 'entrar' ? 'current-password' : 'new-password'} minLength={mode === 'entrar' ? 1 : 8} required /></label>}
    {(mode === 'cadastro' || mode === 'redefinir') && <><label>Confirmar senha<input name="confirmation" type="password" autoComplete="new-password" minLength={8} required /></label><p className="hint">Use pelo menos 8 caracteres.</p></>}
    {mode === 'recuperar' && <label>Solicitação<select aria-label="Solicitação" name="kind" value={kind} onChange={e=>setKind(e.target.value)}><option value="recovery">Recuperar senha</option><option value="confirmation">Reenviar confirmação de cadastro</option></select></label>}
    <SubmitButton>{mode === 'entrar' ? 'Entrar' : mode === 'cadastro' ? 'Criar conta' : mode === 'redefinir' ? 'Atualizar senha' : 'Enviar email'}</SubmitButton>
  </form>;
}
export function RecoveryBridge() {
  const [state, setState] = useState<FormState>({}), [pending, start] = useTransition();
  const router = useRouter();
  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const access = hash.get('access_token'), refresh = hash.get('refresh_token');
    if (!access || !refresh) return;
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
    start(async () => { const result = await establishRecovery(access, refresh); setState(result); if (!result.error) router.refresh(); });
  }, [router]);
  return <><Feedback state={state} />{pending && <p role="status">Verificando o link…</p>}</>;
}
export function DeleteForm({ id }: { id: string }) {
  const [state, dispatch] = useActionState(deleteRoundAction, {} as FormState);
  return <form action={dispatch} className="form-stack delete-form"><input type="hidden" name="id" value={id} /><Feedback state={state} />
    <label className="check-line"><input type="checkbox" name="confirm" value="yes" required />Confirmo a exclusão definitiva desta partida.</label>
    <p className="hint">O campo salvo será mantido na sua biblioteca.</p>
    <SubmitButton className="button danger">Excluir partida</SubmitButton>
  </form>;
}
function ScorecardFields({ n, layout, initial }: { n: number; layout?: Layout; initial?: Round }) {
  const [values, setValues] = useState(() => ({
    par: Array.from({ length: n }, (_, i) => String(layout?.pars[i] ?? '')),
    score: Array.from({ length: n }, (_, i) => String(initial?.scores[i] ?? '')),
    putts: Array.from({ length: n }, (_, i) => String(initial?.putts[i] ?? '')),
    penalty: Array.from({ length: n }, (_, i) => String(initial?.penalties[i] ?? 0)),
    gir: Array.from({ length: n }, (_, i) => !!initial?.girs[i]),
  }));
  const total = values.score.every(v => v !== '') ? sum(values.score.map(Number)) : null;
  function update(field: 'par' | 'score' | 'putts' | 'penalty', i: number, value: string) {
    setValues(prev => ({ ...prev, [field]: prev[field].map((v, j) => j === i ? value : v) }));
  }
  return <><div className="section-line"><h2>Scorecard</h2><span>{total === null ? `${n} buracos` : `Total: ${total} tacadas`}</span></div>
    <p className="hint">O score inclui as penalidades. Preencha os putts com zero se não houve nenhum.</p>
    <div className="score-entry">{Array.from({ length: n }, (_, i) => <div className="hole-row" key={i}>
      <h3><span className="sr-only">Buraco </span>{String(i + 1).padStart(2, '0')}</h3>
      {([{ key: 'par', label: 'Par', min: 3, max: 5 }, { key: 'score', label: 'Score', min: 1 }, { key: 'putts', label: 'Putts', min: 0 }, { key: 'penalty', label: 'Penalidades', min: 0 }] as const).map(f => <label key={f.key}><span>{f.label}</span><input aria-label={`${f.label} do buraco ${i + 1}`} name={`${f.key}_${i}`} type="number" min={f.min} max={'max' in f ? f.max : undefined} step="1" value={values[f.key][i]} onChange={e => update(f.key, i, e.target.value)} required /></label>)}
      <label className="gir-field"><span>GIR</span><input aria-label={`GIR do buraco ${i + 1}`} type="checkbox" name={`gir_${i}`} checked={values.gir[i]} onChange={e => setValues(prev => ({ ...prev, gir: prev.gir.map((v, j) => j === i ? e.target.checked : v) }))} /></label>
    </div>)}</div></>;
}
function RoundFields({ n, layout, initial }: { n: number; layout?: Layout; initial?: Round }) {
  const names = splitCourse(layout?.course ?? '');
  const [base, setBase] = useState({ course: names.name, tee: names.tee, date: initial ? parseDate(initial.date) ?? '' : today(), handicap: String(initial?.handicap ?? ''),
    fairway_opportunities: String(initial?.fairway_opportunities ?? 0), fairways_hit: String(initial?.fairways_hit ?? 0),
    up_and_down_opportunities: String(initial?.up_and_down_opportunities ?? 0), up_and_downs_converted: String(initial?.up_and_downs_converted ?? 0) });
  const update = (key: keyof typeof base, value: string) => setBase(prev => ({ ...prev, [key]: value }));
  return <div className="form-stack"><div className="form-grid">
    <label>Nome do campo<input name="course" value={base.course} onChange={e => update('course',e.target.value)} required maxLength={180} /></label>
    <label>Tee / percurso<input name="tee" value={base.tee} onChange={e => update('tee',e.target.value)} maxLength={100} placeholder="Ex.: Branco, Azul" /></label>
    <label>Data da partida<input name="date" type="date" value={base.date} onChange={e => update('date',e.target.value)} max={today()} min="1900-01-01" required /></label>
    <label>Handicap informado<input name="handicap" type="number" min="-10" max="54" step="0.1" value={base.handicap} onChange={e => update('handicap',e.target.value)} required /></label>
  </div><p className="hint">O handicap é informado por você; não calculamos um índice oficial. Para um handicap +2, informe -2.</p>
  <ScorecardFields n={n} layout={layout} initial={initial} />
  <div className="section-line"><h2>Fairways e jogo curto</h2></div>
  <p className="hint">Conte as oportunidades de fairway apenas nos pares 4 e 5. Para up-and-down, considere os buracos sem GIR. Use zero nas oportunidades quando não registrar essas estatísticas.</p>
  <div className="form-grid">{([{ name: 'fairway_opportunities', label: 'Oportunidades de fairway' }, { name: 'fairways_hit', label: 'Fairways acertados' }, { name: 'up_and_down_opportunities', label: 'Oportunidades de up-and-down' }, { name: 'up_and_downs_converted', label: 'Up-and-downs convertidos' }] as const).map(f => <label key={f.name}>{f.label}<input name={f.name} type="number" min="0" max={n} step="1" value={base[f.name]} onChange={e => update(f.name,e.target.value)} required /></label>)}</div></div>;
}

export function RoundEditor({ choices, initial, preset }: { choices: Layout[]; initial?: Round; preset?: string }) {
  const [selected, setSelected] = useState(preset && choices.some(c => layoutKey(c) === preset) ? preset : ''), [length, setLength] = useState(18), [dirty, setDirty] = useState(false);
  const [state, dispatch] = useActionState(saveRoundAction, {} as FormState);
  const layout = initial ? { course: initial.course, pars: initial.pars } : choices.find(c => layoutKey(c) === selected);
  const n = layout?.pars.length ?? length;
  const context = initial ? `edit-${initial.id}` : `${selected}-${n}`;
  function changeSource(value: string, holes?: number) {
    if (dirty && !window.confirm('Mudar o campo ou a quantidade de buracos apagará os dados deste formulário. Continuar?')) return;
    setDirty(false); setSelected(value); if (holes) setLength(holes);
  }
  return <div>
    {!initial && <div className="form-grid source-picker"><label>Campo salvo<select aria-label="Campo salvo" value={selected} onChange={e => changeSource(e.target.value)}><option value="">Cadastrar um campo novo</option>{choices.map(c => <option key={layoutKey(c)} value={layoutKey(c)}>{c.course} · {c.pars.length} buracos</option>)}</select></label>
      {!layout && <label>Quantidade de buracos<select aria-label="Quantidade de buracos" value={length} onChange={e => changeSource('', Number(e.target.value))}><option value="18">18 buracos</option><option value="9">9 buracos</option></select></label>}</div>}
    <form action={dispatch} className="form-stack" onChange={e => { if ((e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) && e.target.name) setDirty(true); }}>
      <Feedback state={state} />
      {initial && <input type="hidden" name="id" value={initial.id} />}
      <input type="hidden" name="holes" value={n} />
      <RoundFields key={context} n={n} layout={layout} initial={initial} />
      <div className="form-actions"><SubmitButton pendingText="Salvando…">{initial ? 'Salvar alterações' : 'Salvar partida'}</SubmitButton><span className="hint">O campo e seus pares também ficam salvos na sua conta.</span></div>
    </form>
  </div>;
}
export function CourseEditor({ initial }: { initial?: Layout }) {
  const [n, setN] = useState(initial?.pars.length ?? 18);
  const [state, dispatch] = useActionState(saveCourseAction, {} as FormState);
  const names = splitCourse(initial?.course ?? '');
  const [name,setName]=useState(names.name),[tee,setTee]=useState(names.tee);
  return <form action={dispatch} className="form-stack"><Feedback state={state} />
    <div className="form-grid"><label>Nome do campo<input name="course" value={name} onChange={e=>setName(e.target.value)} maxLength={180} required /></label><label>Tee / percurso<input name="tee" value={tee} onChange={e=>setTee(e.target.value)} maxLength={100} placeholder="Ex.: Branco, Azul" /></label>
      <label>Quantidade de buracos<select aria-label="Quantidade de buracos" name="holes" value={n} onChange={e => setN(Number(e.target.value))}><option value="18">18 buracos</option><option value="9">9 buracos</option></select></label></div>
    <ParFields key={`${initial?.course}-${n}`} n={n} initial={initial} />
    <SubmitButton pendingText="Salvando…">Salvar campo</SubmitButton>
    <p className="hint">As próximas partidas usarão estes pares. Os scorecards das partidas anteriores serão preservados.</p>
  </form>;
}
function ParFields({ n, initial }: { n: number; initial?: Layout }) {
  const [pars,setPars]=useState(()=>Array.from({length:n},(_,i)=>String(initial?.pars.length===n?initial.pars[i]:'')));
  return <div className="par-entry">{pars.map((value,i)=><label key={i}>Buraco {i+1}<input name={`par_${i}`} aria-label={`Par do buraco ${i+1}`} type="number" min="3" max="5" step="1" value={value} onChange={e=>setPars(prev=>prev.map((v,j)=>i===j?e.target.value:v))} required /></label>)}</div>;
}
