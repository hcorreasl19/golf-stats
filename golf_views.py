"""Round entry, history, saved layouts, and statistical reporting."""
from datetime import date
import uuid

import interface
import pandas as pd
import streamlit as st

from golf_domain import aggregate, chronological, course_label, hole_analysis, round_date, statistics, templates, today
from golf_repository import CourseRepository


def saved_layouts(rounds):
    return templates(rounds, CourseRepository.from_user(st.session_state.user))


def percent(value):
    return 'No data' if value is None else f'{value:.1f}%'


def start_round(round_id=None, template=None):
    st.session_state.edit_round_id = round_id
    st.session_state.rounds_section = 'Record round'
    st.session_state.preset_course = template
    st.session_state.editor_epoch = uuid.uuid4().hex


def notify(message):
    st.session_state.round_notice = message


def round_name(r):
    return f"{r['date']} · {r['course']} · {len(r['pars'])} holes · {sum(r['scores'])} strokes"


def filter_rounds(rounds, prefix, length_required=False):
    lengths = sorted({len(r['pars']) for r in rounds})
    a, b = st.columns(2)
    courses = sorted({r['course'] for r in rounds}, key=str.casefold)
    course = a.selectbox('Course and tee', ['All courses'] + courses, key=f'{prefix}_course')
    lengths_options = lengths if length_required else ['All lengths'] + lengths
    length = b.selectbox('Round length', lengths_options, key=f'{prefix}_length', format_func=lambda x: f'{x} holes' if isinstance(x, int) else x)
    filtered = [r for r in rounds if (course == 'All courses' or r['course'] == course)
                and (length == 'All lengths' or len(r['pars']) == length)]
    with st.expander('Date and score filters'):
        a, b = st.columns(2)
        since = a.date_input('From', value=None, min_value=date(1900, 1, 1), key=f'{prefix}_since')
        until = b.date_input('To', value=None, min_value=date(1900, 1, 1), key=f'{prefix}_until')
        query = st.text_input('Search course, date or total score', key=f'{prefix}_search').strip().casefold()
    if since and until and since > until:
        st.error('The start date must be on or before the end date.')
        return []
    result = []
    for r in filtered:
        try:
            day = round_date(r['date'])
        except ValueError:
            day = None
        if (since or until) and (day is None or (since and day < since) or (until and day > until)):
            continue
        if query and query not in f"{r['course']} {r['date']} {sum(r['scores'])}".casefold():
            continue
        result.append(r)
    return chronological(result)


def history(rounds, repository):
    st.subheader('Your round history')
    if not rounds:
        st.info('No rounds yet. Record your first round to save its course and hole pars.')
        st.button('Record your first round', on_click=start_round, type='primary')
        return
    filtered = filter_rounds(rounds, 'history')
    if not filtered:
        st.info('No rounds match these filters.')
        return
    records = []
    for r in reversed(filtered):
        s = statistics(r)
        records.append({'Date': r['date'], 'Course / tee': r['course'], 'Holes': s['holes'],
                        'Score': s['score'], 'To par': f"{s['to_par']:+d}", 'Putts': s['putts'],
                        'GIR': percent(s['gir']), 'Fairways': percent(s['fairways'])})
    st.dataframe(pd.DataFrame(records), hide_index=True, width='stretch')
    by_id = {str(r['id']): r for r in filtered}
    selected = st.selectbox('Select a round to review or edit', list(reversed(by_id)),
                            format_func=lambda rid: round_name(by_id[rid]), key='history_round')
    r = by_id[selected]
    st.dataframe(pd.DataFrame({'Hole': range(1, len(r['pars']) + 1), 'Par': r['pars'],
                               'Score': r['scores'], 'Putts': r['putts'], 'GIR': r['girs'],
                               'Penalties': r['penalties']}), hide_index=True, width='stretch')
    st.button('Edit this round', on_click=start_round, args=(r['id'],), type='primary')
    with st.expander('Delete this round'):
        st.write(round_name(r))
        confirmed = st.checkbox('I understand this deletion cannot be undone.', key=f'delete_confirm_{r["id"]}')
        if st.button('Permanently delete selected round', disabled=not confirmed, key=f'delete_{r["id"]}'):
            try:
                repository.delete(r['id'])
            except Exception:
                st.error('The round could not be deleted. Nothing has been confirmed; please refresh and try again.')
            else:
                notify('Round deleted.')
                st.rerun()


def saved_courses(rounds):
    st.subheader('Saved courses & tees')
    st.write('The first saved round remembers its course, tee and hole pars. Select that layout next time and enter only your round statistics.')
    layouts = saved_layouts(rounds)
    course_layout_form(layouts)
    if not layouts:
        st.info('Add a layout above or save your first round to remember its hole pars.')
        return
    label = st.selectbox('Saved layout', sorted(layouts, key=str.casefold), key='library_layout')
    layout = layouts[label]
    st.caption(f"{len(layout['pars'])} holes · Par {sum(layout['pars'])}")
    st.dataframe(pd.DataFrame({'Hole': range(1, len(layout['pars']) + 1), 'Par': layout['pars']}), hide_index=True, width='stretch')
    st.button('Play this course', on_click=start_round, kwargs={'template': label}, type='primary')
    if st.button('Save layout to my account'):
        try:
            updated_user = CourseRepository(interface.client(), st.session_state.user.id).save(layout['course'], layout['pars'])
            st.session_state.user = updated_user
        except Exception:
            st.error('The course library could not be synced. Your round history is unchanged. Please try again.')
        else:
            st.success('Layout saved independently of your rounds.')
    st.caption('Layouts are saved privately to your account and survive deleting rounds. Older rounds keep their own scorecards. Legacy layouts are also recovered from your history.')


def course_layout_form(layouts):
    with st.expander('Add or update a course layout'):
        selected = st.selectbox('Layout to configure', ['New layout'] + sorted(layouts), key='library_edit')
        layout = layouts.get(selected)
        n = len(layout['pars']) if layout else st.selectbox('Course length', [18, 9], key='library_length')
        name, tee = (layout['course'].rsplit(' · Tee: ', 1) if layout and ' · Tee: ' in layout['course']
                     else (layout['course'] if layout else '', ''))
        with st.form(f'layout_form_{selected}_{n}'):
            name = st.text_input('Course name', value=name, key=f'layout_name_{selected}_{n}')
            tee = st.text_input('Tee / layout name', value=tee, key=f'layout_tee_{selected}_{n}')
            pars = []
            columns = st.columns(3)
            for i in range(n):
                pars.append(columns[i % 3].number_input(f'Hole {i + 1} par', min_value=3, max_value=5,
                            value=layout['pars'][i] if layout else None, key=f'layout_par_{selected}_{n}_{i}'))
            save = st.form_submit_button('Save course layout', type='primary')
        if save:
            try:
                label = course_label(name, tee)
                if any(p is None for p in pars):
                    raise ValueError('Complete the par for every hole.')
            except ValueError as exc:
                st.error(str(exc))
            else:
                try:
                    updated_user = CourseRepository(interface.client(), st.session_state.user.id).save(label, pars)
                    st.session_state.user = updated_user
                except Exception:
                    st.error('The course layout could not be saved. Please try again; your round history is unchanged.')
                else:
                    notify('Course layout saved to your account. It is ready to select when recording a round.')
                    st.rerun()


def editor(rounds, repository):
    layouts = saved_layouts(rounds)
    editing_id = st.session_state.get('edit_round_id')
    existing = next((r for r in rounds if r['id'] == editing_id), None) if editing_id is not None else None
    if editing_id is not None and existing is None:
        st.warning('This round is no longer available. Start a new round from History.')
        return
    st.subheader('Edit round' if existing else 'Record a round')
    if existing:
        layout = {'course': existing['course'], 'pars': existing['pars']}
        selected = f'edit-{editing_id}'
        n = len(existing['pars'])
        st.caption('Editing a round updates that record only. Other saved rounds are preserved.')
    else:
        options = ['New course / layout'] + sorted(layouts, key=str.casefold)
        preset = st.session_state.get('preset_course')
        epoch = st.session_state.get('editor_epoch', 'initial')
        selected = st.selectbox('Use a saved course or create a new one', options,
                                index=options.index(preset) if preset in options else 0,
                                key=f'course_selection_{epoch}')
        layout = layouts.get(selected)
        n = len(layout['pars']) if layout else st.selectbox('Number of holes', [18, 9], key=f'new_length_{epoch}')
    epoch = st.session_state.get('editor_epoch', 'initial')
    key = f'editor_{epoch}_{selected}_{n}'
    name, tee = (layout['course'].rsplit(' · Tee: ', 1) if layout and ' · Tee: ' in layout['course']
                 else (layout['course'] if layout else '', ''))
    try:
        day = round_date(existing['date']) if existing else today()
    except ValueError:
        day = today()
        st.warning('The old date is invalid. Select the correct date before saving.')
    with st.form(key):
        a, b = st.columns(2)
        name = a.text_input('Course name', value=name)
        tee = b.text_input('Tee / layout name', value=tee, help='For example White, Blue or Championship. Different tees are saved separately.')
        a, b = st.columns(2)
        played = a.date_input('Date played', value=day, min_value=date(1900, 1, 1), max_value=max(today(), day))
        handicap = b.number_input('Handicap index (manual)', min_value=-10.0, max_value=54.0,
                                  value=float(existing['handicap']) if existing else None,
                                  help='This is your own supplied index, not an official WHS calculation. Enter -2 for a plus-2 handicap.')
        st.caption('Score is the total strokes including penalties. Putts and penalty strokes must already be included in that total. Complete every hole; scores and putts are never invented.')
        pars, scores, putts, girs, penalties = [], [], [], [], []
        for i in range(n):
            with st.expander(f'Hole {i + 1:02d}', expanded=i == 0):
                a, b, c, d = st.columns(4)
                par = a.number_input('Par', min_value=3, max_value=5,
                                     value=layout['pars'][i] if layout else None, key=f'{key}_par_{i}')
                score = b.number_input('Score', min_value=1, value=existing['scores'][i] if existing else None, key=f'{key}_score_{i}')
                putt = c.number_input('Putts', min_value=0, value=existing['putts'][i] if existing else None, key=f'{key}_putts_{i}')
                penalty = d.number_input('Penalty strokes', min_value=0, value=existing['penalties'][i] if existing else 0, key=f'{key}_penalties_{i}')
                gir = st.checkbox('Green in regulation', value=bool(existing['girs'][i]) if existing else False, key=f'{key}_gir_{i}')
                pars.append(par); scores.append(score); putts.append(putt); penalties.append(penalty); girs.append(int(gir))
        st.subheader('Fairways & short game')
        st.caption('Fairways: count opportunities on par-4 and par-5 holes only. Up-and-down: count attempts on holes without GIR. Leave opportunities and successes at zero when not tracked; reports show No data.')
        a, b = st.columns(2)
        fw_opp = a.number_input('Fairway opportunities', min_value=0, max_value=n, value=existing['fairway_opportunities'] if existing else 0)
        fw_hit = b.number_input('Fairways hit', min_value=0, max_value=n, value=existing['fairways_hit'] if existing else 0)
        a, b = st.columns(2)
        ud_opp = a.number_input('Up-and-down opportunities', min_value=0, max_value=n, value=existing['up_and_down_opportunities'] if existing else 0)
        ud_hit = b.number_input('Up-and-downs converted', min_value=0, max_value=n, value=existing['up_and_downs_converted'] if existing else 0)
        submitted = st.form_submit_button('Save changes' if existing else 'Save round', type='primary')
    if submitted:
        try:
            data = {'course': course_label(name, tee), 'date': played.isoformat(), 'handicap': handicap,
                    'pars': pars, 'scores': scores, 'putts': putts, 'girs': girs, 'penalties': penalties,
                    'fairway_opportunities': fw_opp, 'fairways_hit': fw_hit,
                    'up_and_down_opportunities': ud_opp, 'up_and_downs_converted': ud_hit}
            from golf_domain import validate_round
            validate_round(data)
        except ValueError as exc:
            st.error(str(exc))
        else:
            try:
                repository.save(data, existing['id'] if existing else None)
            except Exception:
                st.error('The save could not be confirmed. Your form is intact. Check History before retrying to avoid duplicates.')
            else:
                try:
                    updated_user = CourseRepository(repository.client, repository.user_id).save(data['course'], data['pars'])
                    st.session_state.user = updated_user
                except Exception:
                    notify('Round saved. The course is available from History, but its independent library copy could not be synced. Use Save layout in Saved courses to retry.')
                else:
                    notify('Changes saved.' if existing else 'Round saved. This course and its hole pars are ready for next time.')
                st.session_state.edit_round_id = None
                st.session_state.pending_rounds_section = 'History'
                st.session_state.editor_epoch = uuid.uuid4().hex
                st.rerun()
    st.button('Start a fresh round', on_click=start_round)


def my_rounds(rounds, repository):
    st.title('My rounds')
    if notice := st.session_state.pop('round_notice', None):
        st.success(notice)
    if pending := st.session_state.pop('pending_rounds_section', None):
        st.session_state.rounds_section = pending
    section = st.radio('Round workspace', ['History', 'Record round', 'Saved courses'], horizontal=True, key='rounds_section')
    if section == 'History':
        history(rounds, repository)
    elif section == 'Record round':
        editor(rounds, repository)
    else:
        saved_courses(rounds)


def reports(rounds):
    st.title('Statistics')
    st.caption('Compare like-for-like rounds. Handicap values are manually recorded; this site does not calculate an official handicap index.')
    if not rounds:
        st.info('No rounds yet. Sign in and save a round to see your statistics.')
        return
    rows = filter_rounds(rounds, 'stats', length_required=True)
    if not rows:
        st.info('No rounds match these filters.')
        return
    totals = aggregate(rows)
    a, b, c, d = st.columns(4)
    a.metric('Rounds', len(rows)); b.metric('Average score', f"{totals['score']:.1f}")
    c.metric('Average to par', f"{totals['to_par']:+.1f}"); d.metric('Average putts', f"{totals['putts']:.1f}")
    a, b, c = st.columns(3)
    a.metric('GIR', percent(totals['gir'])); b.metric('Fairways', percent(totals['fairways'])); c.metric('Up-and-down', percent(totals['up_down']))
    st.caption('Percentages use total successes / total opportunities across the selected rounds, rather than an average of percentages.')
    overview, courses, holes, records = st.tabs(['Progress', 'Courses', 'Holes', 'Personal records'])
    with overview:
        metric = st.selectbox('Trend', ['Score', 'To par', 'Putts', 'Handicap (manual)', 'GIR %', 'Fairways %', 'Penalties'])
        names = {'Score': 'score', 'To par': 'to_par', 'Putts': 'putts', 'GIR %': 'gir', 'Fairways %': 'fairways', 'Penalties': 'penalties'}
        points = []
        invalid_dates = 0
        for r in rows:
            try:
                day = round_date(r['date'])
            except ValueError:
                invalid_dates += 1
                continue
            s = statistics(r)
            value = r['handicap'] if metric == 'Handicap (manual)' else s[names[metric]]
            points.append({'Date': pd.Timestamp(day), metric: value})
        if invalid_dates:
            st.warning(f'{invalid_dates} round(s) have invalid legacy dates and are omitted from the chart. Edit those dates in My rounds.')
        if points:
            st.line_chart(pd.DataFrame(points), x='Date', y=metric, width='stretch')
            st.caption('Rounds are sorted by date played. Missing measurements remain gaps, not zero scores.')
        st.subheader('Scoring by hole par')
        a, b, c = st.columns(3)
        for col, p in zip((a, b, c), (3, 4, 5)):
            value = totals[f'par{p}']
            col.metric(f'Par {p} average', f'{value:.2f}' if value is not None else 'No data')
    with courses:
        data = []
        for identity in sorted({(r['course'], tuple(r['pars'])) for r in rows}):
            group = [r for r in rows if (r['course'], tuple(r['pars'])) == identity]
            stats = aggregate(group)
            data.append({'Course / tee': identity[0], 'Holes': len(identity[1]), 'Par': sum(identity[1]),
                         'Rounds': len(group), 'Average score': round(stats['score'], 1),
                         'Average to par': round(stats['to_par'], 1), 'GIR': percent(stats['gir']), 'Fairways': percent(stats['fairways'])})
        st.dataframe(pd.DataFrame(data), hide_index=True, width='stretch')
    with holes:
        identities = list(dict.fromkeys((r['course'], tuple(r['pars'])) for r in rows))
        chosen = st.selectbox('Course / tee / scorecard', range(len(identities)),
                              format_func=lambda i: f'{identities[i][0]} · {len(identities[i][1])} holes · Par {sum(identities[i][1])} · layout {i + 1}')
        selected = [r for r in rows if (r['course'], tuple(r['pars'])) == identities[chosen]]
        data = hole_analysis(selected)
        st.dataframe(pd.DataFrame(data), hide_index=True, width='stretch')
        a, b = st.columns(2)
        a.subheader('Hardest holes'); b.subheader('Easiest holes')
        for col, ordered in ((a, sorted(data, key=lambda x: x['To par'], reverse=True)), (b, sorted(data, key=lambda x: x['To par']))):
            for row in ordered[:3]:
                col.write(f"Hole {row['Hole']}: {row['To par']:+.2f} to par")
    with records:
        st.caption('Records use the course and round-length filters above. Different course ratings and tees can affect comparability.')
        stats = [statistics(r) for r in rows]
        a, b, c = st.columns(3)
        a.metric('Best score', min(s['score'] for s in stats)); b.metric('Best to par', f"{min(s['to_par'] for s in stats):+d}")
        c.metric('Fewest putts', min(s['putts'] for s in stats))
        distribution = {label: sum(s[key] for s in stats) for label, key in [
            ('Albatross or better', 'albatross_or_better'), ('Eagles', 'eagles'), ('Birdies', 'birdies'),
            ('Pars', 'pars'), ('Bogeys', 'bogeys'), ('Double bogeys', 'doubles'), ('Triple bogey or worse', 'triples_plus')]}
        st.bar_chart(pd.DataFrame({'Holes': distribution}), width='stretch')
        st.dataframe(pd.DataFrame([{'Result': k, 'Holes': v} for k, v in distribution.items()]), hide_index=True, width='stretch')
