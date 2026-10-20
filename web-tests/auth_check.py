"""Additional local-only auth integration checks (same test servers as browser_check.py)."""
from urllib.request import Request,urlopen
import json
from playwright.sync_api import sync_playwright

urlopen(Request('http://127.0.0.1:8900/test/reset',method='POST')).read()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page()
    page.goto('http://127.0.0.1:3000/conta?modo=cadastro')
    page.get_by_label('Email',exact=True).fill('player@example.test')
    page.get_by_label('Senha',exact=True).fill('test-password')
    page.get_by_label('Confirmar senha',exact=True).fill('different-password')
    page.get_by_role('button',name='Criar conta',exact=True).click()
    page.get_by_text('As senhas não coincidem.',exact=True).wait_for()
    assert page.get_by_label('Email',exact=True).input_value()=='player@example.test'
    page.get_by_label('Senha',exact=True).fill('test-password')
    page.get_by_label('Confirmar senha',exact=True).fill('test-password')
    page.get_by_role('button',name='Criar conta',exact=True).click()
    page.get_by_text('Confira seu email para confirmar o cadastro. Depois, entre na sua conta.',exact=True).wait_for()
    page.goto('http://127.0.0.1:3000/conta')
    page.get_by_label('Email',exact=True).fill('player@example.test')
    page.get_by_label('Senha',exact=True).fill('wrong-password')
    page.get_by_role('button',name='Entrar',exact=True).click()
    page.get_by_role('alert').wait_for()
    assert page.get_by_label('Email',exact=True).input_value()=='player@example.test'
    session=json.load(urlopen(Request('http://127.0.0.1:8900/auth/v1/verify',data=b'{}',headers={'Content-Type':'application/json'},method='POST')))
    page.goto('http://127.0.0.1:3000/auth/callback#access_token='+session['access_token']+'&refresh_token='+session['refresh_token']+'&type=recovery')
    page.get_by_label('Nova senha',exact=True).wait_for(timeout=20000)
    assert 'access_token' not in page.url
    assert page.url.startswith('http://127.0.0.1:3000/')
    print('Additional browser checks passed: signup confirmation, mismatched passwords, bad-login email retained, default fragment recovery, same-host redirect. Local backend only.')
    browser.close()
