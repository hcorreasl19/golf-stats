"""Validation and statistics independent of Streamlit and the database."""
from datetime import date, datetime
from zoneinfo import ZoneInfo


def today():
    return datetime.now(ZoneInfo('America/Sao_Paulo')).date()


def round_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for pattern in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(str(value)[:10], pattern).date()
        except ValueError:
            pass
    raise ValueError('Use a valid round date.')


def chronological(rounds):
    def key(r):
        try:
            return round_date(r['date']), str(r.get('id', ''))
        except (ValueError, KeyError):
            return date.min, str(r.get('id', ''))
    return sorted(rounds, key=key)


def course_label(name, tee):
    name, tee = ' '.join(name.split()), ' '.join(tee.split())
    if not name:
        raise ValueError('Enter a course name.')
    if ' · Tee: ' in name or ' · Tee: ' in tee:
        raise ValueError('Use a course or tee name without the reserved separator.')
    return f'{name} · Tee: {tee}' if tee else name


def templates(rounds, saved=None):
    """Latest played layout per course, tee and length; legacy names stay intact."""
    result = {}
    for r in chronological(rounds):
        pars = r.get('pars') or []
        if len(pars) in (9, 18) and all(p in (3, 4, 5) for p in pars):
            label = f"{r['course']} / {len(pars)} holes"
            result[label] = {'course': r['course'], 'pars': list(pars)}
    for layout in saved or []:
        label = f"{layout['course']} / {len(layout['pars'])} holes"
        result[label] = {'course': layout['course'], 'pars': list(layout['pars'])}
    return result


def ratio(hits, opportunities):
    return hits / opportunities * 100 if opportunities else None


def validate_round(r):
    if not r.get('course', '').strip():
        raise ValueError('Enter a course name.')
    if round_date(r.get('date')) > today():
        raise ValueError('A completed round cannot have a future date.')
    n = len(r.get('pars') or [])
    if n not in (9, 18):
        raise ValueError('A round must contain 9 or 18 holes.')
    for field in ('pars', 'scores', 'putts', 'girs', 'penalties'):
        values = r.get(field)
        if not isinstance(values, list) or len(values) != n or any(v is None for v in values):
            raise ValueError(f'Complete {field} for all {n} holes.')
        if any(not isinstance(v, int) or isinstance(v, bool) for v in values):
            raise ValueError(f'Invalid values in {field}.')
    for i, (par, score, putts, gir, penalty) in enumerate(zip(r['pars'], r['scores'], r['putts'], r['girs'], r['penalties']), 1):
        if par not in (3, 4, 5) or score < 1 or putts < 0 or penalty < 0 or gir not in (0, 1):
            raise ValueError(f'Check the values for hole {i}.')
        if putts + penalty > score:
            raise ValueError(f'Hole {i}: putts plus penalty strokes cannot exceed the score.')
    handicap = r.get('handicap')
    if handicap is None or not -10 <= handicap <= 54:
        raise ValueError('Enter a handicap between -10 and 54 (use a negative number for a plus handicap).')
    for hit, opp, maximum in (
        ('fairways_hit', 'fairway_opportunities', sum(p > 3 for p in r['pars'])),
        ('up_and_downs_converted', 'up_and_down_opportunities', n),
    ):
        h, o = r.get(hit), r.get(opp)
        if not isinstance(h, int) or not isinstance(o, int) or not 0 <= h <= o <= maximum:
            raise ValueError(f'Check {hit.replace("_", " ")} and opportunities (maximum {maximum}).')
    if r['up_and_down_opportunities'] > n - sum(r['girs']):
        raise ValueError('Up-and-down opportunities cannot exceed holes without GIR.')
    return r


def statistics(r):
    scores, pars = r['scores'], r['pars']
    diffs = [s - p for s, p in zip(scores, pars)]
    return {
        'holes': len(pars), 'score': sum(scores), 'par': sum(pars), 'to_par': sum(diffs),
        'putts': sum(r['putts']), 'penalties': sum(r['penalties']),
        'gir': ratio(sum(r['girs']), len(pars)),
        'fairways': ratio(r['fairways_hit'], r['fairway_opportunities']),
        'up_down': ratio(r['up_and_downs_converted'], r['up_and_down_opportunities']),
        'albatross_or_better': sum(d <= -3 for d in diffs),
        'eagles': diffs.count(-2), 'birdies': diffs.count(-1), 'pars': diffs.count(0),
        'bogeys': diffs.count(1), 'doubles': diffs.count(2), 'triples_plus': sum(d >= 3 for d in diffs),
        'front_nine': sum(scores[:9]), 'back_nine': sum(scores[9:]) if len(scores) == 18 else None,
    }


def aggregate(rounds):
    if not rounds:
        return {}
    stats = [statistics(r) for r in rounds]
    result = {name: sum(s[name] for s in stats) / len(stats) for name in ('score', 'putts', 'to_par')}
    result.update({
        'gir': ratio(sum(sum(r['girs']) for r in rounds), sum(len(r['pars']) for r in rounds)),
        'fairways': ratio(sum(r['fairways_hit'] for r in rounds), sum(r['fairway_opportunities'] for r in rounds)),
        'up_down': ratio(sum(r['up_and_downs_converted'] for r in rounds), sum(r['up_and_down_opportunities'] for r in rounds)),
    })
    for par in (3, 4, 5):
        values = [s for r in rounds for p, s in zip(r['pars'], r['scores']) if p == par]
        result[f'par{par}'] = sum(values) / len(values) if values else None
    return result


def hole_analysis(rounds):
    # Never combine distinct courses, tees, or 9/18-hole layouts.
    identities = {(r['course'].casefold(), len(r['pars']), tuple(r['pars'])) for r in rounds}
    if len(identities) > 1:
        raise ValueError('Select one course, tee and layout before comparing holes.')
    if not rounds:
        return []
    result = []
    for i in range(len(rounds[0]['pars'])):
        result.append({'Hole': i + 1, 'Par': rounds[0]['pars'][i],
                       'Score': sum(r['scores'][i] for r in rounds) / len(rounds),
                       'To par': sum(r['scores'][i] - r['pars'][i] for r in rounds) / len(rounds),
                       'Putts': sum(r['putts'][i] for r in rounds) / len(rounds),
                       'GIR %': ratio(sum(r['girs'][i] for r in rounds), len(rounds))})
    return result
