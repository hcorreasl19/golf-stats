import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'golf_stats_v9.py')).run(timeout=20)
        self.assertFalse(app.exception)
        return app

    def go(self, app, page):
        app.radio[0].set_value(page).run()
        self.assertFalse(app.exception)
        return app

    def test_public_home_without_secrets(self):
        with patch('interface.create_client') as create:
            app = self.app()
            self.assertTrue(any('Every round.' in item.value for item in app.markdown))
            create.assert_not_called()

    def test_all_visitor_pages_without_database(self):
        with patch('interface.create_client') as create:
            app = self.app()
            for page in app.radio[0].options:
                self.go(app, page)
            create.assert_not_called()

    def test_visitor_save_gate_opens_account(self):
        app = self.go(self.app(), 'Enter Round')
        app.button[-1].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.radio[0].value, 'Account')
        self.assertEqual(len(app.text_input), 5)

    def test_registration_validation_prevents_request(self):
        with patch('interface.client') as client:
            app = self.go(self.app(), 'Account')
            app.text_input(key='register_email').set_value('player@example.com')
            app.text_input(key='register_password').set_value('long-password')
            app.text_input[-1].set_value('different-password')
            app.button[-1].click().run()
            self.assertIn('do not match', app.error[0].value)
            client.assert_not_called()

    def test_registration_email_confirmation(self):
        with patch('interface.client') as client:
            client.return_value.auth.sign_up.return_value = SimpleNamespace(session=None, user=None)
            app = self.go(self.app(), 'Account')
            app.text_input(key='register_email').set_value('player@example.com')
            app.text_input(key='register_password').set_value('long-password')
            app.text_input[-1].set_value('long-password')
            app.button[-1].click().run()
            self.assertFalse(app.exception)
            self.assertIn('confirmation link', app.success[0].value)
            client.return_value.auth.sign_up.assert_called_once()
            self.assertIsNone(app.session_state.user)

    def test_login_logout(self):
        with patch('interface.client') as client:
            client.return_value.auth.sign_in_with_password.return_value = SimpleNamespace(
                user=SimpleNamespace(id='player-id', email='player@example.com'), session=object())
            app = self.go(self.app(), 'Account')
            app.text_input(key='login_email').set_value('player@example.com')
            app.text_input(key='login_password').set_value('long-password')
            app.button[1].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state.user.id, 'player-id')
            next(b for b in app.button if b.label == 'Sign out').click().run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state.user)
            self.assertEqual(app.radio[0].value, 'Home')

    def test_failed_login_is_handled(self):
        with patch('interface.client') as client:
            client.return_value.auth.sign_in_with_password.side_effect = ConnectionError('private diagnostic')
            app = self.go(self.app(), 'Account')
            app.text_input(key='login_email').set_value('player@example.com')
            app.text_input(key='login_password').set_value('long-password')
            app.button[1].click().run()
            self.assertFalse(app.exception)
            self.assertIn('Unable to connect', app.error[0].value)
            self.assertNotIn('private diagnostic', app.error[0].value)

    def test_authenticated_round_form_and_user_scoped_query(self):
        with patch('interface.client') as client:
            query = client.return_value.table.return_value.select.return_value
            query.eq.return_value.order.return_value.execute.return_value.data = []
            app = self.app()
            app.session_state.user = SimpleNamespace(id='player-id', email='player@example.com')
            self.go(app, 'Enter Round')
            self.assertEqual(len(app.expander), 18)
            self.assertTrue(any(b.label == 'Save Round' for b in app.button))
            query.eq.assert_called_with('user_id', 'player-id')

    def test_auth_client_is_not_shared_between_sessions(self):
        with patch('interface.create_client') as create:
            for _ in range(2):
                app = self.go(self.app(), 'Account')
                app.secrets['supabase'] = {'url': 'https://example.supabase.co', 'key': 'test-only'}
                app.text_input(key='login_email').set_value('player@example.com')
                app.text_input(key='login_password').set_value('long-password')
                create.return_value.auth.sign_in_with_password.return_value = SimpleNamespace(user=None, session=None)
                app.button[1].click().run()
                self.assertFalse(app.exception)
            self.assertEqual(create.call_count, 2)


if __name__ == '__main__':
    unittest.main()
