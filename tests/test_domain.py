import copy
import unittest
from datetime import timedelta
from golf_domain import aggregate, chronological, course_label, hole_analysis, round_date, statistics, templates, today, validate_round


def sample(n=18, **changes):
    row = dict(id=1, course='Links', date='2025-03-01', handicap=12.0,
               pars=[4]*n, scores=[4]*n, putts=[2]*n, girs=[1]*n, penalties=[0]*n,
               fairway_opportunities=n, fairways_hit=n//2,
               up_and_down_opportunities=0, up_and_downs_converted=0)
    row.update(changes)
    return row


class DomainTests(unittest.TestCase):
    def test_exact_scoring_categories(self):
        r = sample(9, pars=[5,5,4,4,4,4,4,4,4], scores=[2,3,3,4,5,6,7,8,4], girs=[0]*9)
        s = statistics(r)
        self.assertEqual([s[k] for k in ('albatross_or_better','eagles','birdies','pars','bogeys','doubles','triples_plus')], [1,1,1,2,1,1,2])

    def test_nine_hole_denominator_and_no_back_nine(self):
        s = statistics(sample(9, girs=[1]*3+[0]*6))
        self.assertAlmostEqual(s['gir'], 100/3)
        self.assertIsNone(s['back_nine'])

    def test_missing_opportunities_are_not_zero_percent(self):
        r = sample(fairway_opportunities=0, fairways_hit=0)
        self.assertIsNone(statistics(r)['fairways'])
        self.assertIsNone(statistics(r)['up_down'])
        self.assertIsNone(aggregate([r])['fairways'])

    def test_percentages_are_weighted_and_missing_excluded(self):
        a = sample(fairway_opportunities=1, fairways_hit=1)
        b = sample(fairway_opportunities=9, fairways_hit=0)
        c = sample(fairway_opportunities=0, fairways_hit=0)
        self.assertEqual(aggregate([a,b,c])['fairways'], 10)

    def test_par_average_counts_holes_not_rounds(self):
        a = sample(9, pars=[3]+[4]*8, scores=[6]+[4]*8)
        b = sample(9, pars=[3]*3+[4]*6, scores=[3]*3+[4]*6)
        self.assertEqual(aggregate([a,b])['par3'], 3.75)
        self.assertIsNone(aggregate([a,b])['par5'])

    def test_legacy_and_iso_dates_sort_by_played_date(self):
        rows=[sample(id=1,date='20/12/2024'),sample(id=2,date='2024-01-02'),sample(id=3,date='invalid')]
        self.assertEqual([r['id'] for r in chronological(rows)], [3,2,1])
        with self.assertRaises(ValueError): round_date('31/02/2025')

    def test_future_date_rejected(self):
        with self.assertRaises(ValueError): validate_round(sample(date=(today()+timedelta(days=1)).isoformat()))

    def test_incomplete_round_rejected(self):
        for field in ('pars','scores','putts','girs','penalties'):
            r=sample();r[field][2]=None
            with self.subTest(field=field),self.assertRaises(ValueError): validate_round(r)

    def test_only_nine_or_eighteen_complete_holes(self):
        with self.assertRaises(ValueError): validate_round(sample(10))
        self.assertEqual(len(validate_round(sample(9))['scores']),9)

    def test_impossible_putts_or_penalties_rejected(self):
        for updates in ({'putts':[5]*18}, {'penalties':[3]*18}):
            with self.subTest(updates=updates),self.assertRaises(ValueError): validate_round(sample(**updates))

    def test_gir_can_precede_additional_non_putting_strokes(self):
        # A player can hit GIR, putt off the green and need another chip.
        self.assertEqual(validate_round(sample(scores=[7]*18,putts=[3]*18))['girs'],[1]*18)

    def test_fairway_success_cannot_exceed_opportunities(self):
        with self.assertRaises(ValueError): validate_round(sample(fairway_opportunities=1,fairways_hit=2))
        with self.assertRaises(ValueError): validate_round(sample(pars=[3]*18,girs=[0]*18))

    def test_up_and_down_conflicting_with_gir_rejected(self):
        with self.assertRaises(ValueError): validate_round(sample(up_and_down_opportunities=1,up_and_downs_converted=1))

    def test_plus_handicap_is_allowed(self):
        self.assertEqual(validate_round(sample(handicap=-2.0))['handicap'],-2.0)

    def test_course_name_and_tee_normalization(self):
        self.assertEqual(course_label('  Ocean   Links ', ' White  '),'Ocean Links · Tee: White')
        with self.assertRaises(ValueError): course_label('  ','White')

    def test_course_templates_survive_reload_and_keep_tee_length_separate(self):
        rows=[sample(id=1,course='Links · Tee: Blue'),sample(9,id=2,course='Links · Tee: Blue'),sample(id=3,course='Links · Tee: White')]
        saved=templates(copy.deepcopy(rows))
        self.assertEqual(len(saved),3)
        self.assertEqual(saved['Links · Tee: Blue / 9 holes']['pars'],[4]*9)

    def test_newest_played_layout_used_without_mutating_history(self):
        old=sample(id=10,date='2024-01-01');new=sample(id=2,date='2025-01-01',pars=[3]*18)
        self.assertEqual(templates([new,old])['Links / 18 holes']['pars'],[3]*18)
        self.assertEqual(old['pars'],[4]*18)

    def test_hole_analysis_separates_courses_tees_and_layouts(self):
        for b in (sample(course='Other'),sample(9),sample(pars=[3]*18)):
            with self.subTest(course=b['course']),self.assertRaises(ValueError): hole_analysis([sample(),b])
        self.assertEqual(len(hole_analysis([sample(9)])),9)


if __name__=='__main__': unittest.main()
