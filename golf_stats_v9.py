"""Streamlit entry point. Existing filename retained for deployed applications."""
import streamlit as st
from interface import account, client, footer, header, home, navigate, styles, handle_auth_link
from golf_repository import RoundRepository
from golf_views import my_rounds, reports

st.set_page_config(page_title='Golf Stats', layout='wide')
styles()
st.session_state.setdefault('user', None)
handle_auth_link()
page = header()

if page == 'Home':
    home()
elif page == 'Account':
    account()
elif st.session_state.user is None:
    st.title('My rounds' if page == 'My rounds' else 'Statistics')
    st.info('Explore the site freely. Sign in or create an account to save rounds and see your personal statistics.')
    st.button('Sign in / Create account', type='primary', on_click=navigate, args=('Account',))
else:
    try:
        repository = RoundRepository(client(), st.session_state.user.id)
        rounds = repository.load()
    except Exception:
        st.error('Your rounds could not be loaded. Please try again shortly. No records have been changed.')
    else:
        usable = []
        for row in rounds:
            n = len(row.get('pars') or [])
            fields = ('pars', 'scores', 'putts', 'girs', 'penalties')
            if n in (9, 18) and all(isinstance(row.get(k), list) and len(row[k]) == n
                                  and all(isinstance(v, (int, float)) for v in row[k]) for k in fields):
                usable.append(row)
        if len(usable) != len(rounds):
            st.warning(f'{len(rounds) - len(usable)} incomplete legacy record(s) were excluded from reports. They have not been deleted.')
        if page == 'My rounds':
            my_rounds(usable, repository)
        else:
            reports(usable)
footer()
