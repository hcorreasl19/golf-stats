"""Public pages and account UI for Golf Stats."""
from html import escape
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import streamlit as st
from streamlit.components.v1 import declare_component
from supabase import create_client
from supabase_auth.errors import AuthApiError


_auth_callback = declare_component('golf_auth_callback', path=str(Path(__file__).with_name('auth_callback')))


PAGES = ["Home", "My rounds", "Statistics", "Account"]


def client():
    # Auth sessions must never be shared through st.cache_resource.
    if "supabase_client" not in st.session_state:
        credentials = st.secrets["supabase"]
        st.session_state.supabase_client = create_client(credentials["url"], credentials["key"])
    return st.session_state.supabase_client


def styles():
    css = Path(__file__).with_name('style.css').read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def header():
    left, right = st.columns([4, 1], vertical_alignment="center")
    with left:
        st.markdown('<div class="wordmark">GOLF<span>STATS</span><small>THE GAME, IN PERSPECTIVE</small></div>', unsafe_allow_html=True)
    with right:
        label = "My account" if st.session_state.user else "Sign in / Register"
        if st.button(label, width='stretch'):
            st.session_state.navigation = "Account"
    st.radio("Navigation", PAGES, horizontal=True, key="navigation", label_visibility="collapsed", width="stretch")
    return st.session_state.navigation


def home():
    st.markdown('''<section class="hero">
      <div class="hero-copy"><p class="eyebrow">A CLOSER LOOK AT YOUR GAME</p>
      <h1>Every round.<br>A clearer perspective.</h1>
      <p class="hero-description">Keep a record of your rounds. Understand where you gain strokes,
      where you lose them, and how your game changes over time.</p>
      <a class="editorial-link" href="#explore">Explore Golf Stats <span>↘</span></a></div>
      <div class="course-art" aria-hidden="true"><div class="contour contour-one"></div>
      <div class="contour contour-two"></div><div class="contour contour-three"></div>
      <div class="green"></div><div class="flag"><i></i></div><span class="art-caption">A GAME OF DETAILS.</span>
      <span class="hole-mark">18<span>HOLES. ONE COMPLETE PICTURE.</span></span></div>
    </section>''', unsafe_allow_html=True)
    a, b, _ = st.columns([1.3, 1.3, 3])
    with a:
        st.button("View statistics", on_click=navigate, args=("Statistics",), type="primary", width='stretch')
    with b:
        st.button("Create an account", on_click=navigate, args=("Account",), width='stretch')
    st.markdown('''<section id="explore" class="intro"><p class="eyebrow">YOUR ROUND, BEYOND THE SCORECARD</p>
      <h2>A record worth<br>coming back to.</h2><p>From the first tee to the last putt,
      bring the details of your game together in one place.</p></section>
      <div class="feature-grid"><article><span>01 / RECORD</span><h3>Capture the round.</h3>
      <p>Scores, putts, greens in regulation and fairways. A hole-by-hole record of what happened on the course.</p></article>
      <article><span>02 / UNDERSTAND</span><h3>Find the patterns.</h3><p>Compare courses, review individual holes and follow the numbers that matter to your game.</p></article>
      <article><span>03 / REVIEW</span><h3>See your progress.</h3><p>Keep your history close. Revisit personal bests and track your performance across rounds.</p></article></div>''', unsafe_allow_html=True)


def navigate(page):
    st.session_state.navigation = page


def handle_auth_link():
    """Consume one-time Supabase token-hash/PKCE callbacks without retaining URLs."""
    recovered = _auth_callback(key='golf_auth_link', consumed=st.session_state.get('auth_link_consumed'), default=None)
    if isinstance(recovered, dict) and recovered.get('access_token') and recovered.get('refresh_token'):
        digest = sha256(recovered['access_token'].encode()).hexdigest()
        if digest != st.session_state.get('auth_link_consumed'):
            st.session_state.auth_link_consumed = digest
            st.session_state.navigation = 'Account'
            try:
                response = client().auth.set_session(recovered['access_token'], recovered['refresh_token'])
                if not response.user or not response.session:
                    raise ValueError('Unverified session')
                st.session_state.user = response.user
                st.session_state.recovering = recovered.get('type') == 'recovery'
                st.session_state.auth_notice = 'Link verified. Set your new password below.' if st.session_state.recovering else 'Email verified. You are signed in.'
            except Exception:
                st.session_state.auth_notice = 'This link could not be verified. Request a new email in Account help.'
            st.rerun()
    params = st.query_params
    token_hash = params.get('token_hash')
    code = params.get('code')
    auth_type = params.get('type')
    if not token_hash and not code:
        return
    st.query_params.clear()
    st.session_state.navigation = 'Account'
    try:
        if token_hash and auth_type in ('recovery', 'signup', 'email'):
            response = client().auth.verify_otp({'token_hash': token_hash, 'type': auth_type})
        elif code:
            response = client().auth.exchange_code_for_session({'auth_code': code})
        else:
            raise ValueError('Unsupported confirmation link')
        if not response.user or not response.session:
            raise ValueError('No verified session')
        st.session_state.user = response.user
        st.session_state.recovering = auth_type == 'recovery'
        st.session_state.auth_notice = 'Email verified. You are signed in.'
    except Exception:
        st.session_state.auth_notice = 'This link could not be verified. Use Account help to request a new email.'


def recovery_password():
    st.subheader('Set a new password')
    with st.form('verified_new_password'):
        password = st.text_input('New password', type='password')
        confirmation = st.text_input('Confirm new password', type='password')
        submit = st.form_submit_button('Update password', type='primary')
    if submit:
        if len(password) < 8 or password != confirmation:
            st.error('Use at least 8 characters and matching passwords.')
        else:
            try:
                client().auth.update_user({'password': password})
            except Exception:
                st.error('The password could not be updated. Request a fresh recovery email and try again.')
            else:
                st.session_state.recovering = False
                st.session_state.auth_notice = 'Password updated. You can now use your new password.'
                st.rerun()


def account_help():
    st.subheader('Account help')
    with st.form('account_email_help'):
        email = st.text_input('Account email', key='help_email')
        action = st.selectbox('What do you need?', ['Reset password', 'Resend confirmation email'])
        send = st.form_submit_button('Send email')
    if send:
        if '@' not in email or not email.strip():
            st.error('Enter a valid email address.')
        else:
            try:
                if action == 'Reset password':
                    client().auth.reset_password_for_email(email.strip())
                else:
                    client().auth.resend({'type': 'signup', 'email': email.strip()})
            except Exception:
                st.error('The email request could not be completed. Please try again later.')
            else:
                st.success('If the account is eligible, an email will arrive shortly. Check your spam folder too.')
    with st.expander('Finish a password reset'):
        st.write('Open the recovery email link. If it does not show a password form, copy the complete address from the page it opens and paste it below. You can also use a recovery code if your email includes one. Never share this link or code.')
        with st.form('recovery_link'):
            email = st.text_input('Recovery email')
            token = st.text_input('Recovery link or code', type='password', autocomplete='off')
            password = st.text_input('New password', type='password', key='recovery_new')
            confirmation = st.text_input('Confirm new password', type='password', key='recovery_confirm')
            finish = st.form_submit_button('Verify and update password', type='primary')
        if finish:
            if not token or len(password) < 8 or password != confirmation:
                st.error('Provide the recovery link/code and matching passwords of at least 8 characters.')
            else:
                try:
                    parts = urlsplit(token)
                    fragment, query = parse_qs(parts.fragment), parse_qs(parts.query)
                    if 'access_token' in fragment and 'refresh_token' in fragment:
                        response = client().auth.set_session(fragment['access_token'][0], fragment['refresh_token'][0])
                    elif 'token_hash' in query:
                        response = client().auth.verify_otp({'token_hash': query['token_hash'][0], 'type': 'recovery'})
                    elif token.isdigit() and '@' in email:
                        response = client().auth.verify_otp({'email': email.strip(), 'token': token.strip(), 'type': 'recovery'})
                    else:
                        raise ValueError('Unsupported recovery credentials')
                    if not response.user or not response.session:
                        raise ValueError('Recovery was not verified')
                    client().auth.update_user({'password': password})
                except Exception:
                    st.error('Recovery could not be completed. The link may be expired or already used. Request a new email.')
                else:
                    st.session_state.user = response.user
                    st.session_state.recovering = False
                    st.session_state.auth_notice = 'Password updated. You are signed in.'
                    st.rerun()


def account():
    if notice := st.session_state.pop('auth_notice', None):
        st.info(notice)
    if st.session_state.get('recovering') and st.session_state.user:
        recovery_password()
        return
    if st.session_state.user:
        st.title("Your account")
        st.write(escape(st.session_state.user.email or "Signed in"))
        if st.button("Sign out", type="primary"):
            try:
                client().auth.sign_out()
            except Exception:
                st.warning("The connection could not be closed remotely. Your local session has been cleared.")
            consumed = st.session_state.get('auth_link_consumed')
            st.session_state.clear()
            st.session_state.auth_link_consumed = consumed
            st.rerun()
        return
    copy, form = st.columns([1.2, 1], gap="large")
    with copy:
        st.markdown('''<div class="account-copy"><p class="eyebrow">YOUR PERSONAL RECORD</p>
        <h1>Make room<br>for your game.</h1><p>Explore the site freely. Create an account to save your rounds
        and keep your statistics together.</p></div>''', unsafe_allow_html=True)
    with form:
        login, register, help_tab = st.tabs(["Sign in", "Create account", "Account help"])
        with login:
            with st.form("login"):
                st.subheader("Welcome back")
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign in", type="primary", width='stretch')
            if submit:
                if not email.strip() or not password:
                    st.error("Enter your email and password.")
                else:
                    try:
                        response = client().auth.sign_in_with_password({"email": email.strip(), "password": password})
                        if response.user and response.session:
                            st.session_state.user = response.user
                            st.rerun()
                        else:
                            st.error("Sign-in could not be completed. Check your email and password.")
                    except AuthApiError:
                        st.error("Sign-in failed. Check your details and confirm your email if required.")
                    except Exception:
                        st.error("Unable to connect. Please try again shortly.")
        with register:
            with st.form("register"):
                st.subheader("Start your record")
                new_email = st.text_input("Email", key="register_email")
                new_password = st.text_input("Password", type="password", key="register_password", help="Use at least 8 characters.")
                confirm = st.text_input("Confirm password", type="password")
                create = st.form_submit_button("Create account", type="primary", width='stretch')
            if create:
                if not new_email.strip() or "@" not in new_email:
                    st.error("Enter a valid email address.")
                elif len(new_password) < 8:
                    st.error("Use at least 8 characters for your password.")
                elif new_password != confirm:
                    st.error("The passwords do not match.")
                else:
                    try:
                        response = client().auth.sign_up({"email": new_email.strip(), "password": new_password})
                        if response.session and response.user:
                            st.session_state.user = response.user
                            st.rerun()
                        else:
                            st.success("Check your email for a confirmation link. Once confirmed, return here to sign in.")
                    except AuthApiError:
                        st.error("Registration could not be completed. Try signing in if you already have an account, or check the password requirements.")
                    except Exception:
                        st.error("Unable to connect. Please try again shortly.")

        with help_tab:
            account_help()


def footer():
    st.markdown('<footer><strong>GOLF STATS</strong><span>A record of the game you play.</span><span>RECORD / UNDERSTAND / REVIEW</span></footer>', unsafe_allow_html=True)
