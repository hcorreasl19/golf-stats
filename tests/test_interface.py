import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from pathlib import Path
from streamlit.testing.v1 import AppTest
from test_domain import sample

APP=str(Path(__file__).resolve().parents[1]/'golf_stats_v9.py')


class InterfaceTests(unittest.TestCase):
    def app(self,user=False):
        app=AppTest.from_file(APP)
        if user:
            app.session_state.user=SimpleNamespace(id='player-id',email='player@example.com')
            app.session_state.supabase_client=MagicMock()
        app.run(timeout=30)
        self.assertFalse(app.exception)
        return app

    def go(self,app,page):
        app.radio(key='navigation').set_value(page).run()
        self.assertFalse(app.exception)
        return app

    def button(self,app,label):
        return next(b for b in app.button if b.label==label)

    def test_public_navigation_without_credentials(self):
        with patch('interface.create_client') as create:
            app=self.app()
            for page in ['Home','My rounds','Statistics','Account']:
                self.go(app,page)
            create.assert_not_called()

    def test_guest_gate_opens_account(self):
        app=self.go(self.app(),'My rounds')
        self.button(app,'Sign in / Create account').click().run()
        self.assertEqual(app.radio(key='navigation').value,'Account')
        self.assertFalse(app.exception)

    def test_registration_validation_and_email_confirmation(self):
        with patch('interface.client') as client:
            client.return_value.auth.sign_up.return_value=SimpleNamespace(session=None,user=None)
            app=self.go(self.app(),'Account')
            app.text_input(key='register_email').set_value('player@example.com')
            app.text_input(key='register_password').set_value('long-password')
            next(x for x in app.text_input if x.label=='Confirm password').set_value('different')
            self.button(app,'Create account').click().run()
            self.assertIn('do not match',app.error[0].value)
            client.assert_not_called()
            next(x for x in app.text_input if x.label=='Confirm password').set_value('long-password')
            self.button(app,'Create account').click().run()
            self.assertIn('confirmation link',app.success[0].value)
            client.return_value.auth.sign_up.assert_called_once()

    def test_login_logout_and_network_errors(self):
        with patch('interface.client') as client:
            app=self.go(self.app(),'Account')
            app.text_input(key='login_email').set_value('player@example.com')
            app.text_input(key='login_password').set_value('long-password')
            client.return_value.auth.sign_in_with_password.side_effect=ConnectionError('private')
            self.button(app,'Sign in').click().run()
            self.assertIn('Unable to connect',app.error[0].value)
            client.return_value.auth.sign_in_with_password.side_effect=None
            client.return_value.auth.sign_in_with_password.return_value=SimpleNamespace(user=SimpleNamespace(id='player-id',email='player@example.com'),session=object())
            self.button(app,'Sign in').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state.user.id,'player-id')
            self.button(app,'Sign out').click().run()
            self.assertIsNone(app.session_state.user)

    def test_blank_round_cannot_save_and_nine_holes_supported(self):
        with patch('golf_repository.RoundRepository.load',return_value=[]),patch('golf_repository.RoundRepository.save') as save:
            app=self.go(self.app(user=True),'My rounds')
            app.radio(key='rounds_section').set_value('Record round').run()
            self.assertEqual(len(app.expander),18)
            self.assertIsNone(next(x for x in app.number_input if x.label=='Score').value)
            next(x for x in app.selectbox if x.label=='Number of holes').set_value(9).run()
            self.assertEqual(len(app.expander),9)
            self.button(app,'Save round').click().run()
            self.assertTrue(app.error)
            save.assert_not_called()

    def test_saved_course_preloads_only_pars_and_keeps_tee(self):
        row=sample(9,course='Links · Tee: White',pars=[3,4,5]*3,girs=[0]*9,fairway_opportunities=0,fairways_hit=0)
        with patch('golf_repository.RoundRepository.load',return_value=[row]):
            app=self.go(self.app(user=True),'My rounds')
            app.radio(key='rounds_section').set_value('Saved courses').run()
            self.button(app,'Play this course').click().run()
            self.assertFalse(app.exception)
            self.assertEqual([x.value for x in app.number_input if x.label=='Par'],row['pars'])
            self.assertTrue(all(x.value is None for x in app.number_input if x.label in ('Score','Putts')))
            self.assertEqual(next(x.value for x in app.text_input if x.label=='Tee / layout name'),'White')

    def test_save_first_round_reuses_template_after_rerender(self):
        rows=[]
        with patch('golf_repository.RoundRepository.load',side_effect=lambda _: rows,autospec=True),patch('golf_repository.RoundRepository.save',autospec=True) as save:
            def persist(repo,data,round_id=None):
                rows.append(dict(data,id=42));return [rows[-1]]
            save.side_effect=persist
            app=self.go(self.app(user=True),'My rounds')
            app.radio(key='rounds_section').set_value('Record round').run()
            next(x for x in app.selectbox if x.label=='Number of holes').set_value(9).run()
            next(x for x in app.text_input if x.label=='Course name').set_value('New Links')
            for x in app.number_input:
                if x.label=='Par': x.set_value(4)
                elif x.label=='Score': x.set_value(5)
                elif x.label=='Putts': x.set_value(2)
                elif x.label=='Handicap index (manual)': x.set_value(12.0)
            self.button(app,'Save round').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(rows),1)
            self.assertEqual(app.radio(key='rounds_section').value,'History')
            app.radio(key='rounds_section').set_value('Saved courses').run()
            self.button(app,'Play this course').click().run()
            self.assertFalse(app.exception)
            self.assertEqual([x.value for x in app.number_input if x.label=='Par'],[4]*9)
            self.assertTrue(all(x.value is None for x in app.number_input if x.label=='Score'))

    def test_edit_round_preserves_hole_data(self):
        row=sample(9)
        with patch('golf_repository.RoundRepository.load',return_value=[row]),patch('golf_repository.RoundRepository.save') as save:
            app=self.go(self.app(user=True),'My rounds')
            self.button(app,'Edit this round').click().run()
            self.assertFalse(app.exception)
            next(x for x in app.number_input if x.label=='Score').set_value(5)
            next(x for x in app.checkbox if x.label=='Green in regulation').uncheck()
            self.button(app,'Save changes').click().run()
            self.assertFalse(app.exception)
            data,rid=save.call_args.args
            self.assertEqual(rid,row['id']);self.assertEqual(data['scores'],[5]+[4]*8)

    def test_delete_requires_confirmation(self):
        with patch('golf_repository.RoundRepository.load',return_value=[sample()]),patch('golf_repository.RoundRepository.delete') as delete:
            app=self.go(self.app(user=True),'My rounds')
            self.assertTrue(self.button(app,'Permanently delete selected round').disabled)
            next(x for x in app.checkbox if 'cannot be undone' in x.label).check().run()
            self.button(app,'Permanently delete selected round').click().run()
            delete.assert_called_once_with(1)
            self.assertFalse(app.exception)

    def test_reports_render_all_sections_for_nine_holes(self):
        with patch('golf_repository.RoundRepository.load',return_value=[sample(9)]):
            app=self.go(self.app(user=True),'Statistics')
            self.assertFalse(app.exception)
            self.assertEqual([x.label for x in app.tabs],['Progress','Courses','Holes','Personal records'])

    def test_reset_email_and_resend_confirmation(self):
        with patch('interface.client') as client:
            app=self.go(self.app(),'Account')
            app.text_input(key='help_email').set_value('player@example.com')
            self.button(app,'Send email').click().run()
            client.return_value.auth.reset_password_for_email.assert_called_once_with('player@example.com')
            next(x for x in app.selectbox if x.label=='What do you need?').set_value('Resend confirmation email')
            app.text_input(key='help_email').set_value('player@example.com')
            self.button(app,'Send email').click().run()
            client.return_value.auth.resend.assert_called_once()

    def test_recovery_verifies_session_before_password_update(self):
        with patch('interface.client') as client:
            client.return_value.auth.set_session.return_value=SimpleNamespace(user=SimpleNamespace(id='player-id',email='player@example.com'),session=object())
            app=self.go(self.app(),'Account')
            next(x for x in app.text_input if x.label=='Recovery link or code').set_value('https://example.test/#access_token=test-only&refresh_token=test-only')
            app.text_input(key='recovery_new').set_value('long-password')
            app.text_input(key='recovery_confirm').set_value('long-password')
            self.button(app,'Verify and update password').click().run()
            client.return_value.auth.set_session.assert_called_once_with('test-only','test-only')
            client.return_value.auth.update_user.assert_called_once_with({'password':'long-password'})
            self.assertFalse(app.exception)

    def test_course_library_can_be_saved_before_any_round(self):
        user=SimpleNamespace(id='player-id',email='player@example.com',user_metadata={'golf_course_layouts_v1':[{'course':'New Links · Tee: Blue','pars':[4]*9}]})
        with patch('golf_repository.RoundRepository.load',return_value=[]),patch('golf_repository.CourseRepository.save',return_value=user) as save_course,patch('golf_repository.RoundRepository.save') as save_round:
            app=self.go(self.app(user=True),'My rounds')
            app.radio(key='rounds_section').set_value('Saved courses').run()
            next(x for x in app.selectbox if x.label=='Course length').set_value(9).run()
            next(x for x in app.text_input if x.label=='Course name').set_value('New Links')
            next(x for x in app.text_input if x.label=='Tee / layout name').set_value('Blue')
            for x in app.number_input: x.set_value(4)
            self.button(app,'Save course layout').click().run()
            self.assertFalse(app.exception)
            save_course.assert_called_once_with('New Links · Tee: Blue',[4]*9)
            save_round.assert_not_called()
            self.button(app,'Play this course').click().run()
            self.assertEqual([x.value for x in app.number_input if x.label=='Par'],[4]*9)

    def test_failed_round_save_preserves_form_and_does_not_save_template(self):
        with patch('golf_repository.RoundRepository.load',return_value=[sample(9)]),patch('golf_repository.RoundRepository.save',side_effect=ConnectionError),patch('golf_repository.CourseRepository.save') as save_course:
            app=self.go(self.app(user=True),'My rounds')
            self.button(app,'Edit this round').click().run()
            self.button(app,'Save changes').click().run()
            self.assertFalse(app.exception)
            self.assertIn('could not be confirmed',app.error[0].value)
            self.assertEqual([x.value for x in app.number_input if x.label=='Score'],[4]*9)
            save_course.assert_not_called()

    def test_automatic_recovery_callback_is_not_replayed_after_signout(self):
        token={'access_token':'test-only','refresh_token':'test-only','type':'recovery'}
        user=SimpleNamespace(id='player-id',email='player@example.com')
        with patch('interface._auth_callback',return_value=token),patch('interface.client') as client:
            client.return_value.auth.set_session.return_value=SimpleNamespace(user=user,session=object())
            app=self.app()
            self.assertTrue(app.session_state.recovering)
            self.assertEqual(app.radio(key='navigation').value,'Account')
            app.session_state.recovering=False
            app.run()
            self.button(app,'Sign out').click().run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state.user)
            client.return_value.auth.set_session.assert_called_once()

    def test_auth_clients_are_per_session(self):
        with patch('interface.create_client') as create:
            create.return_value.auth.sign_in_with_password.return_value=SimpleNamespace(user=None,session=None)
            for _ in range(2):
                app=self.go(self.app(),'Account')
                app.secrets['supabase']={'url':'https://example.supabase.co','key':'test-only'}
                app.text_input(key='login_email').set_value('player@example.com')
                app.text_input(key='login_password').set_value('long-password')
                self.button(app,'Sign in').click().run()
                self.assertFalse(app.exception)
            self.assertEqual(create.call_count,2)
