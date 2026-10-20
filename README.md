# Golf Stats — web

Next.js / React application for golf rounds, saved course scorecards and statistics.
The new application runs on Node.js; it does not use Streamlit or Python at runtime.
It uses the existing Supabase project, accounts, `rounds` table and private course
metadata, so records do not need to be copied to another database.

## Development

Use Node.js 22 or 24:

```sh
npm ci
cp .env.example .env.local
# Fill SUPABASE_URL and SUPABASE_KEY securely in .env.local.
npm run dev
```

The public home page renders without Supabase configuration. Account features need:

| Variable | Value |
| --- | --- |
| `SUPABASE_URL` | `https://imuoleorggmphkczfkey.supabase.co` |
| `SUPABASE_KEY` | The existing project's publishable/anon key; never `service_role`. |

These variables are server-only. Supabase sessions are verified on the server and
stored in HttpOnly, SameSite=Lax cookies (Secure in production). The browser never
receives the server configuration. All database reads and mutations use the
signed-in user's ID and the user's Supabase session, without bypassing RLS.

```sh
npm run typecheck
npm test
npm run build
npm start
```

## Deploy on Vercel

The repository root contains `package.json`, `package-lock.json` and `vercel.json`.
No Python runtime or separate backend service is required for the new app.

1. In Vercel, choose **Add New → Project**, import `hcorreasl19/golf-stats`, branch
   `main`, and keep the root directory as `./` and framework as **Next.js**.
2. Before deploying, add the two server environment variables from the table above.
   Enter the key securely in Vercel's settings, not in a commit or chat. These
   values are not automatically copied from Codex or the old Streamlit deployment.
3. Click **Deploy**. The build uses `npm ci` and `npm run build`.
4. In Supabase → Authentication → URL Configuration, set **Site URL** to the new
   production HTTPS URL and add `https://YOUR-PROJECT.vercel.app/auth/callback`
   (or `https://YOUR-PROJECT.vercel.app/**`) to **Redirect URLs**. Use your actual
   project domain; configure additional preview domains only if needed.
5. Verify signup, confirmation email, login and recovery with your own test account.
   The same existing email/password and records should work on the new site.

The `streamlit.app` address cannot serve a Next.js application. The new app needs
its Vercel URL or a custom domain. Connect a custom domain through Vercel when
ready. Importing the project creates the deployment; pushing code alone does not
connect a previously unconfigured Vercel account.

## Existing data and features

- Public home page, separate login/signup, confirmation-email resend and recovery.
- Native 9/18-hole scorecards with no invented scores or putts, validation before
  saving, editing, and explicit confirmation before deletion.
- Saved course/tee layouts use the same `golf_course_layouts_v1` Supabase Auth user
  metadata as the earlier version. Layouts are independent of round deletion;
  historical rounds supply compatibility fallback layouts. Metadata is never used
  for authorization.
- The existing course text format `Name · Tee: White` and original numeric arrays
  are preserved. Dates save as ISO; legacy `DD/MM/YYYY` remains readable.
- Distinct scoring categories, opportunity-weighted percentages, real played-date
  trends, separate 9/18-hole comparisons, and course/tee/scorecard-specific holes.
- Zero opportunities mean **Sem dados**, not a misleading 0%.
- Handicap is supplied manually, including plus handicaps as negative numbers.
  No official WHS or rating-adjusted index is calculated.
- Server errors retain the entry form. After an ambiguous insert response, check
  History before retrying. A course-sync failure after a saved round is reported
  separately so users do not insert the round again.

Keep RLS enabled on `rounds`. Authenticated users need SELECT, INSERT, UPDATE and
DELETE policies restricted to `auth.uid() = user_id`; UPDATE also needs an owner
WITH CHECK condition. The migration does not change the table, its policies, or
existing records. Incomplete legacy rows are reported and left untouched.

Supabase Auth email links use `/auth/callback` with PKCE or token-hash verification.
Default implicit recovery links are also accepted: their URL fragments are removed
in the browser, then exchanged server-side into HttpOnly cookies. Email delivery,
rate limits, password policies and redirect allowlists remain Supabase settings.

## Tests

`npm test` executes the pure TypeScript golf-rule tests.

For a local browser integration test, use the provided mock Supabase server and a
Next development server. No real accounts, emails or database writes are used:

```sh
# Terminal 1: local HTTP double
python web-tests/mock_supabase.py

# Terminal 2: use test-only bindings for this process, not a real project
SUPABASE_URL=http://127.0.0.1:8900 SUPABASE_KEY=test-only npm run dev -- --hostname 127.0.0.1 --port 3000

# Terminal 3: requires Playwright Python and Chromium installed in the test machine
python web-tests/browser_check.py
python web-tests/auth_check.py
```

The browser test covers public pages, responsive widths, HttpOnly login, owner
isolation, course persistence, prefilled pars with blank scores, validation,
save/edit/delete, reports, password recovery and logout. Never point this test at
a live Supabase project.

## Streamlit transition

The previous Python entry point is retained temporarily so the existing Streamlit
URL is not broken before Vercel is connected. Its rejected green illustration and
promotional cards have also been removed. These files are not used by `npm run
build` or the new application. The previous Python tests remain available with
`python -m unittest discover -s tests -v`.
