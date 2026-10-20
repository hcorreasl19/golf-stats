"""Public pages and account UI for Golf Stats."""
from html import escape
from pathlib import Path

import streamlit as st
from supabase import create_client
from supabase_auth.errors import AuthApiError


PAGES = ["Home", "Dashboard", "Enter Round", "Round History", "Statistics",
         "Course Analysis", "Hole Analysis", "Graphs", "Personal Records", "Search Rounds", "Account"]


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
        if st.button(label, use_container_width=True):
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
        st.button("View dashboard", on_click=navigate, args=("Dashboard",), type="primary", use_container_width=True)
    with b:
        st.button("Create an account", on_click=navigate, args=("Account",), use_container_width=True)
    st.markdown('''<section id="explore" class="intro"><p class="eyebrow">YOUR ROUND, BEYOND THE SCORECARD</p>
      <h2>A record worth<br>coming back to.</h2><p>From the first tee to the last putt,
      bring the details of your game together in one place.</p></section>
      <div class="feature-grid"><article><span>01 / RECORD</span><h3>Capture the round.</h3>
      <p>Scores, putts, greens in regulation and fairways. A hole-by-hole record of what happened on the course.</p></article>
      <article><span>02 / UNDERSTAND</span><h3>Find the patterns.</h3><p>Compare courses, review individual holes and follow the numbers that matter to your game.</p></article>
      <article><span>03 / REVIEW</span><h3>See your progress.</h3><p>Keep your history close. Revisit personal bests and track your performance across rounds.</p></article></div>''', unsafe_allow_html=True)


def navigate(page):
    st.session_state.navigation = page


def account():
    if st.session_state.user:
        st.title("Your account")
        st.write(escape(st.session_state.user.email or "Signed in"))
        if st.button("Sign out", type="primary"):
            try:
                client().auth.sign_out()
            except Exception:
                st.warning("The connection could not be closed remotely. Your local session has been cleared.")
            st.session_state.clear()
            st.rerun()
        return
    copy, form = st.columns([1.2, 1], gap="large")
    with copy:
        st.markdown('''<div class="account-copy"><p class="eyebrow">YOUR PERSONAL RECORD</p>
        <h1>Make room<br>for your game.</h1><p>Explore the site freely. Create an account to save your rounds
        and keep your statistics together.</p></div>''', unsafe_allow_html=True)
    with form:
        login, register = st.tabs(["Sign in", "Create account"])
        with login:
            with st.form("login"):
                st.subheader("Welcome back")
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
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
                create = st.form_submit_button("Create account", type="primary", use_container_width=True)
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


def footer():
    st.markdown('<footer><strong>GOLF STATS</strong><span>A record of the game you play.</span><span>RECORD / UNDERSTAND / REVIEW</span></footer>', unsafe_allow_html=True)
