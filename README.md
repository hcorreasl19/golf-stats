# Golf Stats

A Streamlit application for 9- and 18-hole golf rounds, saved course scorecards,
round editing, and personal statistics. The public home page needs no account.

## Run locally

Use Python 3.11 or later (validated on Python 3.12):

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run golf_stats_v9.py
```

For account features, configure `.streamlit/secrets.toml` (excluded from Git):

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
key = "YOUR_PUBLISHABLE_OR_ANON_KEY"
```

On Streamlit Community Cloud, put the same TOML in the application's Secrets.
Never use a service-role key. Auth clients are isolated per Streamlit session.

## Saved courses

In **My rounds → Saved courses**, add a course, tee and 9 or 18 hole pars. You can
also save a round first: its layout is saved automatically. Select the saved
layout in **Record round** and only enter your round statistics. Scores and putts
start empty; a previous round's statistics are never copied into a new round.

Layouts are stored privately in the authenticated user's Supabase Auth metadata
under `golf_course_layouts_v1`, independently of rounds. This requires no new
Supabase table or schema migration. Layouts remain after deleting round history.
Existing rounds also supply layouts as a compatibility fallback; use **Save
layout to my account** to retain a historical layout independently. If saving a
round succeeds but saving its layout fails, the app reports the partial outcome
and offers a library retry without inserting another round.

Course and tee identity use the existing `course` text field, formatted as
`Course name · Tee: Tee name`; legacy names remain unchanged. Round length is
inferred from the stored scorecard arrays. Saving a layout changes future entry
only; historical rounds keep their original pars. The latest played historical
layout is used when there is no independently saved layout.

## Accounts and deployment settings

Signup, login, logout, confirmation-email resend and password recovery use
Supabase Auth. If email confirmation is enabled, users must confirm before login.
Configure Supabase Auth **Site URL** to the deployed app URL and its redirect
allowlist accordingly. The app supports one-time `token_hash` callbacks and PKCE
callbacks when their verifier is available. Default implicit recovery links are consumed by the local `auth_callback`
component, which removes the credentials from the browser address. For hosts
that prevent parent-frame access, Account help also accepts the complete recovery destination URL or an
emailed recovery code in a masked field, verifies the session, and updates the
password. Never share those links/codes; recovery tests mock the auth service and
do not send real emails.

The existing `rounds` table must support 9- or 18-element numeric arrays in
`pars`, `scores`, `putts`, `girs`, `penalties`, and the original aggregate counters.
Dates now save in ISO format; existing `DD/MM/YYYY` dates remain readable.

Enable row-level security on `rounds`. Authenticated users need SELECT, INSERT,
UPDATE and DELETE policies restricted to `auth.uid() = user_id`. UPDATE needs
both USING and WITH CHECK owner conditions. The app also filters all reads,
updates and deletes by user ID; filters do not replace RLS. No database policies
or schema are changed automatically by this application.

## Statistics and validation

- Scores include penalty strokes. Putts and penalties cannot exceed total score.
- Birdies, eagles, albatrosses, double bogeys and triples-or-worse are distinct.
- GIR uses the actual 9/18-hole length. A manual GIR flag is retained because
  score minus putts alone cannot establish when the green was first reached.
- Fairway opportunities are limited to par-4/5 holes; conversions cannot exceed
  opportunities. Up-and-down opportunities are limited to holes without GIR.
- Zero opportunities show **No data**, never a misleading 0% success rate.
- Aggregate percentages and par-specific averages weight the actual opportunities
  or holes. Comparisons separate 9 and 18 holes, and hole analysis separates
  courses, tees and exact par layouts.
- Trends use date played, not insertion order. Invalid legacy dates are omitted
  from time charts with a warning and can be corrected through editing.
- Handicap is entered manually (negative values represent plus handicaps).
  No official WHS index or rating-adjusted comparison is calculated.
- Round deletion requires explicit confirmation. Failed saves retain the form;
  after an ambiguous network failure, check History before retrying an insert.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests cover calculations, invalid inputs, weighted statistics, date ordering,
9/18 holes, user isolation, pagination, course-library persistence, saved-par
reuse, editing, confirmed deletion, failed writes, and account flows. Supabase
calls are mocked; no live user accounts or rounds are created or deleted.

`golf_stats_v9.py` is the deployment entry point. Domain rules, persistence and
round UI live in `golf_domain.py`, `golf_repository.py` and `golf_views.py`.
`interface.py` contains public pages and account flows. `style.css` and
`.streamlit/config.toml` provide the responsive theme and rounded controls.
