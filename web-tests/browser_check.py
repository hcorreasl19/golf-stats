"""Run with the local HTTP double and Next dev server; never use a live backend."""
from pathlib import Path
from urllib.request import urlopen, Request
import json
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:3000'
MOCK='http://127.0.0.1:8900'
OUT=Path('/workspace/golf-stats-artifacts/next');OUT.mkdir(parents=True,exist_ok=True)


def state():return json.load(urlopen(MOCK+'/test/state'))


urlopen(Request(MOCK+'/test/reset',method='POST')).read()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1100})
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE)
    page.get_by_role('heading',name='Seu histórico de golfe.').wait_for()
    assert page.locator('main img, main .course-art, main .feature-grid').count()==0
    page.screenshot(path=str(OUT/'home-desktop.png'),full_page=True)
    for w,h in [(390,844),(768,1024)]:
        page.set_viewport_size({'width':w,'height':h})
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    page.screenshot(path=str(OUT/'home-tablet.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'home-mobile.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':1100})
    page.get_by_role('link',name='Registrar uma partida',exact=True).click()
    page.get_by_role('heading',name='Registrar partida',exact=True).wait_for()
    page.get_by_role('link',name='Entrar',exact=True).last.click()
    page.get_by_label('Email',exact=True).fill('player@example.test')
    page.get_by_label('Senha',exact=True).fill('test-password')
    page.get_by_role('button',name='Entrar',exact=True).click()
    page.wait_for_url('**/partidas')
    page.get_by_role('heading',name='Partidas',exact=True).wait_for()
    assert page.get_by_text('Campo de outro usuário',exact=True).count()==0
    assert any(c['httpOnly'] for c in context.cookies() if c['name'].startswith('sb-'))
    assert 'sb-' not in page.evaluate('document.cookie')
    page.get_by_role('navigation',name='Navegação principal').get_by_role('link',name='Campos',exact=True).click()
    page.get_by_label('Nome do campo',exact=True).fill('Clube de Teste')
    page.get_by_label('Tee / percurso',exact=True).fill('Branco')
    page.get_by_label('Quantidade de buracos',exact=True).select_option('9')
    for i in range(9):page.get_by_label(f'Par do buraco {i+1}',exact=True).fill(str([3,4,5][i%3]))
    page.get_by_role('button',name='Salvar campo',exact=True).click()
    page.get_by_text('Campo salvo na sua conta.',exact=True).wait_for()
    course=page.locator('.course-row').filter(has_text='Clube de Teste')
    course.get_by_role('link',name='Jogar neste campo',exact=True).click()
    page.get_by_role('heading',name='Registrar partida',exact=True).wait_for()
    assert [page.get_by_label(f'Par do buraco {i+1}',exact=True).input_value() for i in range(9)]==list(map(str,[3,4,5]*3))
    assert all(page.get_by_label(f'Score do buraco {i+1}',exact=True).input_value()=='' for i in range(9))
    assert all(page.get_by_label(f'Putts do buraco {i+1}',exact=True).input_value()=='' for i in range(9))
    page.get_by_label('Handicap informado',exact=True).fill('12')
    for i in range(9):
        page.get_by_label(f'Score do buraco {i+1}',exact=True).fill(str([4,5,6][i%3]))
        page.get_by_label(f'Putts do buraco {i+1}',exact=True).fill('2')
    page.get_by_label('Score do buraco 1',exact=True).fill('1')
    page.get_by_role('button',name='Salvar partida',exact=True).click()
    page.get_by_role('alert').filter(has_text='putts e penalidades').wait_for()
    assert page.get_by_label('Putts do buraco 1',exact=True).input_value()=='2'
    page.get_by_label('Score do buraco 1',exact=True).fill('4')
    page.get_by_label('Oportunidades de fairway',exact=True).fill('6')
    page.get_by_label('Fairways acertados',exact=True).fill('3')
    page.get_by_role('button',name='Salvar partida',exact=True).click()
    page.wait_for_url('**/partidas/*?salva=1')
    page.get_by_text('Partida salva.',exact=True).wait_for()
    round_url=page.url.split('?')[0]
    page.screenshot(path=str(OUT/'round.png'),full_page=True)
    page.get_by_role('link',name='Editar partida',exact=True).click()
    page.get_by_label('Score do buraco 1',exact=True).fill('5')
    page.get_by_role('button',name='Salvar alterações',exact=True).click()
    page.get_by_text('Partida salva.',exact=True).wait_for()
    data=state();rows=[r for r in data['rows'] if r['course']=='Clube de Teste · Tee: Branco']
    assert len(rows)==1 and rows[0]['scores'][0]==5
    page.get_by_role('navigation',name='Navegação principal').get_by_role('link',name='Estatísticas',exact=True).click()
    page.get_by_role('heading',name='Estatísticas',exact=True).wait_for()
    page.get_by_role('img',name='Evolução de Score por data da partida').wait_for()
    page.screenshot(path=str(OUT/'statistics-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    page.screenshot(path=str(OUT/'statistics-mobile.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':1100})
    page.goto(BASE+'/partidas/900')
    page.get_by_role('heading',name='Registro não encontrado.').wait_for()
    page.goto(round_url)
    page.get_by_text('Excluir esta partida',exact=True).click()
    page.get_by_label('Confirmo a exclusão definitiva desta partida.',exact=True).check()
    page.get_by_role('button',name='Excluir partida',exact=True).click()
    page.wait_for_url('**/partidas?excluida=1')
    data=state()
    assert not any(r['course']=='Clube de Teste · Tee: Branco' for r in data['rows'])
    assert any(c['course']=='Clube de Teste · Tee: Branco' for c in data['metadata']['golf_course_layouts_v1'])
    page.goto(BASE+'/campos')
    page.locator('.course-row').filter(has_text='Clube de Teste').get_by_role('link',name='Jogar neste campo').wait_for()
    page.goto(BASE+'/auth/callback?token_hash=test-only-recovery&type=recovery')
    page.wait_for_url('**/conta?modo=redefinir')
    page.get_by_label('Nova senha',exact=True).fill('new-test-password')
    page.get_by_label('Confirmar senha',exact=True).fill('new-test-password')
    page.get_by_role('button',name='Atualizar senha',exact=True).click()
    page.get_by_text('Senha atualizada. Você já pode usar a nova senha.',exact=True).wait_for()
    assert state()['password_updates']==1
    page.goto(BASE+'/conta')
    page.get_by_role('button',name='Sair da conta',exact=True).click()
    page.wait_for_url(BASE+'/')
    page.goto(BASE+'/partidas')
    page.get_by_role('link',name='Criar uma conta',exact=True).wait_for()
    page.goto(BASE+'/conta?modo=recuperar')
    page.get_by_label('Email',exact=True).fill('player@example.test')
    page.get_by_role('button',name='Enviar email',exact=True).click()
    page.get_by_text('Se a conta estiver apta, o email chegará em instantes. Confira também a pasta de spam.',exact=True).wait_for()
    assert state()['emails']==1
    assert not errors,errors
    print('Browser passed: responsive public pages, login, HttpOnly session, owner isolation, course persistence, blank new stats, validation, save/edit/delete, reports, recovery, logout. Local backend only.')
    browser.close()
