import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace
from golf_repository import RoundRepository
from test_domain import sample


class RepositoryTests(unittest.TestCase):
    def test_requires_user(self):
        with self.assertRaises(ValueError): RoundRepository(MagicMock(),None)

    def test_user_scoped_read_and_pagination(self):
        client=MagicMock();query=client.table.return_value.select.return_value.eq.return_value.order.return_value
        query.range.return_value.execute.side_effect=[SimpleNamespace(data=[sample(id=i) for i in range(500)]),SimpleNamespace(data=[sample(id=501)])]
        rows=RoundRepository(client,'alice').load()
        self.assertEqual(len(rows),501)
        client.table.return_value.select.return_value.eq.assert_called_with('user_id','alice')
        self.assertEqual(query.range.call_args_list[1].args,(500,999))

    def test_insert_binds_owner_and_validates(self):
        client=MagicMock();client.table.return_value.insert.return_value.execute.return_value.data=[sample()]
        repo=RoundRepository(client,'alice');repo.save(sample())
        payload=client.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload['user_id'],'alice');self.assertNotIn('id',payload)
        invalid=sample();invalid['scores'][0]=None
        with self.assertRaises(ValueError): repo.save(invalid)
        self.assertEqual(client.table.return_value.insert.call_count,1)

    def test_update_and_delete_scope_both_record_and_user(self):
        client=MagicMock();query=client.table.return_value.update.return_value
        query.eq.return_value.eq.return_value.execute.return_value.data=[sample()]
        repo=RoundRepository(client,'alice');repo.save(sample(),123)
        query.eq.assert_called_with('id',123)
        query.eq.return_value.eq.assert_called_with('user_id','alice')
        delete=client.table.return_value.delete.return_value
        delete.eq.return_value.eq.return_value.execute.return_value.data=[sample()]
        repo.delete(123)
        delete.eq.assert_called_with('id',123)
        delete.eq.return_value.eq.assert_called_with('user_id','alice')

    def test_empty_save_or_delete_response_is_not_success(self):
        client=MagicMock();client.table.return_value.insert.return_value.execute.return_value.data=[]
        repo=RoundRepository(client,'alice')
        with self.assertRaises(ValueError): repo.save(sample())
        client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data=[]
        with self.assertRaises(ValueError): repo.delete(1)


class CourseRepositoryTests(unittest.TestCase):
    def test_save_merges_existing_layouts_and_preserves_other_metadata(self):
        from golf_repository import CourseRepository
        field=CourseRepository.FIELD
        old={'course':'Old Links','pars':[4]*9}
        client=MagicMock()
        client.auth.get_user.return_value=SimpleNamespace(user=SimpleNamespace(id='alice',user_metadata={field:[old],'display_name':'Alice'}))
        new={'course':'New Links · Tee: Blue','pars':[3,4,5]*6}
        user=SimpleNamespace(id='alice',user_metadata={field:[old,new],'display_name':'Alice'})
        client.auth.update_user.return_value=SimpleNamespace(user=user)
        result=CourseRepository(client,'alice').save(new['course'],new['pars'])
        self.assertEqual(result.user_metadata['display_name'],'Alice')
        payload=client.auth.update_user.call_args.args[0]
        self.assertEqual(payload,{'data':{field:[old,new]}})
        self.assertNotIn('display_name',payload['data'])

    def test_saved_layout_survives_without_any_rounds(self):
        from golf_repository import CourseRepository
        from golf_domain import templates
        user=SimpleNamespace(user_metadata={CourseRepository.FIELD:[{'course':'Links','pars':[4]*9}]})
        self.assertEqual(templates([],CourseRepository.from_user(user))['Links / 9 holes']['pars'],[4]*9)

    def test_wrong_user_cannot_change_course_library(self):
        from golf_repository import CourseRepository
        client=MagicMock();client.auth.get_user.return_value=SimpleNamespace(user=SimpleNamespace(id='bob'))
        with self.assertRaises(ValueError): CourseRepository(client,'alice').save('Links',[4]*9)
        client.auth.update_user.assert_not_called()

    def test_metadata_is_untrusted_and_malformed_layouts_are_ignored(self):
        from golf_repository import CourseRepository
        user=SimpleNamespace(user_metadata={CourseRepository.FIELD:[{'course':'Broken','pars':[4]}, {'course':'Broken','pars':[None]*9}]})
        self.assertEqual(CourseRepository.from_user(user),[])
