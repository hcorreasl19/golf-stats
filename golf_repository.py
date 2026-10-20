"""User-scoped persistence using the existing rounds table; no schema changes."""
from golf_domain import chronological, validate_round

FIELDS = ('course', 'date', 'handicap', 'pars', 'scores', 'putts', 'girs', 'penalties',
          'fairway_opportunities', 'fairways_hit', 'up_and_down_opportunities', 'up_and_downs_converted')


class RoundRepository:
    def __init__(self, client, user_id):
        if not user_id:
            raise ValueError('Sign in to access rounds.')
        self.client, self.user_id = client, str(user_id)

    def load(self):
        rows, offset = [], 0
        while True:
            page = (self.client.table('rounds').select('*').eq('user_id', self.user_id)
                    .order('id').range(offset, offset + 499).execute().data)
            if not isinstance(page, list):
                raise ValueError('Unexpected rounds response.')
            rows.extend(page)
            if len(page) < 500:
                return chronological(rows)
            offset += len(page)

    def save(self, data, round_id=None):
        validate_round(data)
        payload = {k: data[k] for k in FIELDS}
        if round_id is None:
            payload['user_id'] = self.user_id
            response = self.client.table('rounds').insert(payload).execute()
        else:
            response = (self.client.table('rounds').update(payload).eq('id', round_id)
                        .eq('user_id', self.user_id).execute())
        if not response.data:
            raise ValueError('The round was not saved. Check your account permissions and try again.')
        return response.data

    def delete(self, round_id):
        response = (self.client.table('rounds').delete().eq('id', round_id)
                    .eq('user_id', self.user_id).execute())
        if not response.data:
            raise ValueError('No round was deleted. Refresh your history and try again.')


class CourseRepository:
    """Private layouts in user-editable metadata; never used for authorization."""
    FIELD = 'golf_course_layouts_v1'

    @classmethod
    def from_user(cls, user):
        metadata = getattr(user, 'user_metadata', None)
        values = metadata.get(cls.FIELD, []) if isinstance(metadata, dict) else []
        if not isinstance(values, list):
            return []
        return [dict(course=v['course'], pars=list(v['pars'])) for v in values
                if isinstance(v, dict) and isinstance(v.get('course'), str)
                and isinstance(v.get('pars'), list) and len(v['pars']) in (9, 18)
                and all(type(p) is int and p in (3, 4, 5) for p in v['pars'])]

    def __init__(self, client, user_id):
        self.client, self.user_id = client, str(user_id)

    def save(self, course, pars):
        if not isinstance(course, str) or not course.strip() or len(pars) not in (9, 18) or any(type(p) is not int or p not in (3, 4, 5) for p in pars):
            raise ValueError('Complete a course name and 9 or 18 valid hole pars.')
        response = self.client.auth.get_user()
        if not response.user or str(response.user.id) != self.user_id:
            raise ValueError('The course library belongs to a different account.')
        values = self.from_user(response.user)
        values = [v for v in values if (v['course'].casefold(), len(v['pars'])) != (course.casefold(), len(pars))]
        values.append({'course': course, 'pars': list(pars)})
        updated = self.client.auth.update_user({'data': {self.FIELD: values}})
        if (not updated.user or str(updated.user.id) != self.user_id
                or {'course': course, 'pars': list(pars)} not in self.from_user(updated.user)):
            raise ValueError('The saved course could not be confirmed.')
        return updated.user
