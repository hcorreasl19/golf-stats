# Golf Stats

A Streamlit application for recording golf rounds and reviewing personal statistics.

## Run locally

Use Python 3.11 or later:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run golf_stats_v9.py
```

The public home page and visitor navigation do not require credentials. To enable
account creation, login and saved rounds, configure `.streamlit/secrets.toml`
(already excluded from Git):

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
key = "YOUR_PUBLISHABLE_OR_ANON_KEY"
```

Never use a Supabase service-role key in this application. On Streamlit Community
Cloud, put the same TOML structure in the application's Secrets settings.

Account creation uses Supabase Auth. If email confirmation is enabled, users must
follow the confirmation email before signing in. Configure the Supabase Auth Site
URL and redirect allowlist for your deployment. No new authentication provider or
database migration is required by the interface changes.

The existing `rounds` table must have row-level security policies limiting reads,
inserts and deletes to rows whose `user_id` equals `auth.uid()`. Client-side query
filters do not replace these database policies.

## Tests

```sh
python -m unittest discover -s tests -v
```

The tests exercise visitor navigation, account validation, email confirmation,
login/logout, connection failures, user-scoped reads and separate auth clients.
They mock authentication and database calls; they do not create remote accounts.

## Interface

`interface.py` contains public pages and account flows. `style.css` provides the
responsive layout; `.streamlit/config.toml` defines the shared color theme.
Existing golf calculations remain in `golf_stats_v9.py`.
