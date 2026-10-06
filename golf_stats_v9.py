import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


DATA_FILE = "golf_data.json"


# ============================================================
# DATA
# ============================================================

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as file:
                return json.load(file)
        except:
            return []

    return []


def save_data(rounds):
    with open(DATA_FILE, "w") as file:
        json.dump(rounds, file, indent=4)


rounds = load_data()


# ============================================================
# CALCULATIONS
# ============================================================

def round_statistics(round_data):

    pars = round_data["pars"]
    scores = round_data["scores"]
    putts = round_data["putts"]
    girs = round_data["girs"]
    penalties = round_data["penalties"]

    fairway_opportunities = round_data[
        "fairway_opportunities"
    ]

    fairways_hit = round_data[
        "fairways_hit"
    ]

    up_down_opportunities = round_data[
        "up_and_down_opportunities"
    ]

    up_downs = round_data[
        "up_and_downs_converted"
    ]

    total_score = sum(scores)
    total_par = sum(pars)

    score_to_par = total_score - total_par

    total_putts = sum(putts)

    gir_percentage = sum(girs) / 18 * 100

    if fairway_opportunities > 0:
        fairway_percentage = (
            fairways_hit
            / fairway_opportunities
            * 100
        )
    else:
        fairway_percentage = 0

    if up_down_opportunities > 0:
        up_down_percentage = (
            up_downs
            / up_down_opportunities
            * 100
        )
    else:
        up_down_percentage = 0

    front_nine = sum(scores[:9])
    back_nine = sum(scores[9:])

    par3 = []
    par4 = []
    par5 = []

    birdies = 0
    pars_count = 0
    bogeys = 0
    doubles = 0

    for i in range(18):

        if pars[i] == 3:
            par3.append(scores[i])

        elif pars[i] == 4:
            par4.append(scores[i])

        elif pars[i] == 5:
            par5.append(scores[i])

        difference = scores[i] - pars[i]

        if difference <= -1:
            birdies += 1

        elif difference == 0:
            pars_count += 1

        elif difference == 1:
            bogeys += 1

        elif difference >= 2:
            doubles += 1

    def average(values):
        if len(values) == 0:
            return 0

        return sum(values) / len(values)

    return {
        "score": total_score,
        "par": total_par,
        "to_par": score_to_par,
        "putts": total_putts,
        "gir": gir_percentage,
        "fairways": fairway_percentage,
        "penalties": sum(penalties),
        "up_down": up_down_percentage,
        "front_nine": front_nine,
        "back_nine": back_nine,
        "par3": average(par3),
        "par4": average(par4),
        "par5": average(par5),
        "birdies": birdies,
        "pars": pars_count,
        "bogeys": bogeys,
        "doubles": doubles
    }


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Golf Stats",
    page_icon="⛳",
    layout="wide"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⛳ Golf Stats")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Enter Round",
        "Round History",
        "Statistics",
        "Course Analysis",
        "Hole Analysis",
        "Graphs",
        "Personal Records",
        "Search Rounds"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("⛳ Golf Stats Dashboard")

    if not rounds:

        st.info(
            "You don't have any rounds yet. "
            "Go to 'Enter Round' to add your first round."
        )

    else:

        statistics = [
            round_statistics(r)
            for r in rounds
        ]

        average_score = (
            sum(s["score"] for s in statistics)
            / len(statistics)
        )

        best_score = min(
            s["score"] for s in statistics
        )

        average_putts = (
            sum(s["putts"] for s in statistics)
            / len(statistics)
        )

        average_gir = (
            sum(s["gir"] for s in statistics)
            / len(statistics)
        )

        average_fairways = (
            sum(s["fairways"] for s in statistics)
            / len(statistics)
        )

        current_handicap = rounds[-1]["handicap"]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Handicap",
            f"{current_handicap:.1f}"
        )

        col2.metric(
            "Average Score",
            f"{average_score:.1f}"
        )

        col3.metric(
            "Best Score",
            best_score
        )

        col4.metric(
            "Rounds",
            len(rounds)
        )

        st.divider()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average Putts",
            f"{average_putts:.1f}"
        )

        col2.metric(
            "Average GIR",
            f"{average_gir:.1f}%"
        )

        col3.metric(
            "Fairways",
            f"{average_fairways:.1f}%"
        )

        st.subheader("Recent Scores")

        recent_data = []

        for round_data in rounds[-5:]:

            stats = round_statistics(round_data)

            recent_data.append({
                "Date": round_data["date"],
                "Course": round_data["course"],
                "Score": stats["score"],
                "To Par": stats["to_par"],
                "Putts": stats["putts"]
            })

        st.dataframe(
            pd.DataFrame(recent_data),
            use_container_width=True
        )


# ============================================================
# ENTER ROUND
# ============================================================

elif page == "Enter Round":

    st.title("🏌️ Enter New Round")

    course = st.text_input("Course")

    date = st.text_input(
        "Date",
        value=datetime.now().strftime("%d/%m/%Y")
    )

    handicap = st.number_input(
        "Handicap",
        min_value=0.0,
        max_value=54.0,
        value=21.0,
        step=0.1
    )

    st.subheader("Hole-by-Hole")

    hole_data = []

    for hole in range(18):

        st.markdown(
            f"### Hole {hole + 1}"
        )

        col1, col2, col3, col4 = st.columns(4)

        par = col1.number_input(
            "Par",
            min_value=3,
            max_value=5,
            value=4,
            key=f"par_{hole}"
        )

        score = col2.number_input(
            "Score",
            min_value=1,
            max_value=15,
            value=4,
            key=f"score_{hole}"
        )

        putts = col3.number_input(
            "Putts",
            min_value=0,
            max_value=6,
            value=2,
            key=f"putts_{hole}"
        )

        penalties = col4.number_input(
            "Penalties",
            min_value=0,
            max_value=5,
            value=0,
            key=f"penalties_{hole}"
        )

        gir = st.checkbox(
            "GIR",
            key=f"gir_{hole}"
        )

        if par == 4 or par == 5:

            fairway_opportunity = st.checkbox(
                "Fairway opportunity",
                key=f"fwopp_{hole}"
            )

            fairway_hit = st.checkbox(
                "Fairway hit",
                key=f"fwhit_{hole}"
            )

        else:

            fairway_opportunity = False
            fairway_hit = False

        up_down_opportunity = st.checkbox(
            "Up-and-down opportunity",
            key=f"udopp_{hole}"
        )

        up_down_made = st.checkbox(
            "Up-and-down made",
            key=f"udmade_{hole}"
        )

        hole_data.append({
            "par": par,
            "score": score,
            "putts": putts,
            "penalties": penalties,
            "gir": gir,
            "fairway_opportunity":
                fairway_opportunity,
            "fairway_hit":
                fairway_hit,
            "up_down_opportunity":
                up_down_opportunity,
            "up_down_made":
                up_down_made
        })

    if st.button(
        "💾 Save Round",
        type="primary"
    ):

        if course.strip() == "":

            st.error(
                "Please enter a course."
            )

        else:

            pars = []
            scores = []
            putts = []
            girs = []
            penalties = []

            fairway_opportunities = 0
            fairways_hit = 0

            up_down_opportunities = 0
            up_downs_converted = 0

            for hole in hole_data:

                pars.append(hole["par"])
                scores.append(hole["score"])
                putts.append(hole["putts"])
                penalties.append(hole["penalties"])

                if hole["gir"]:
                    girs.append(1)
                else:
                    girs.append(0)

                if hole["fairway_opportunity"]:

                    fairway_opportunities += 1

                    if hole["fairway_hit"]:
                        fairways_hit += 1

                if hole["up_down_opportunity"]:

                    up_down_opportunities += 1

                    if hole["up_down_made"]:
                        up_downs_converted += 1

            new_round = {
                "course": course,
                "date": date,
                "handicap": handicap,
                "pars": pars,
                "scores": scores,
                "putts": putts,
                "girs": girs,
                "penalties": penalties,
                "fairway_opportunities":
                    fairway_opportunities,
                "fairways_hit":
                    fairways_hit,
                "up_and_down_opportunities":
                    up_down_opportunities,
                "up_and_downs_converted":
                    up_downs_converted
            }

            rounds.append(new_round)

            save_data(rounds)

            st.success(
                "Round saved successfully!"
            )

            stats = round_statistics(
                new_round
            )

            st.metric(
                "Score",
                stats["score"]
            )

            st.metric(
                "To Par",
                f"{stats['to_par']:+d}"
            )


# ============================================================
# ROUND HISTORY
# ============================================================

elif page == "Round History":

    st.title("📋 Round History")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        history = []

        for index, round_data in enumerate(rounds):

            stats = round_statistics(
                round_data
            )

            history.append({
                "#": index + 1,
                "Date": round_data["date"],
                "Course": round_data["course"],
                "Score": stats["score"],
                "To Par": stats["to_par"],
                "Putts": stats["putts"],
                "GIR": f"{stats['gir']:.1f}%",
                "Fairways":
                    f"{stats['fairways']:.1f}%"
            })

        st.dataframe(
            pd.DataFrame(history),
            use_container_width=True
        )

        st.divider()

        st.subheader("Delete a Round")

        round_number = st.number_input(
            "Round number",
            min_value=1,
            max_value=len(rounds),
            step=1
        )

        if st.button(
            "Delete Round",
            type="secondary"
        ):

            rounds.pop(round_number - 1)

            save_data(rounds)

            st.success(
                "Round deleted."
            )

            st.rerun()


# ============================================================
# STATISTICS
# ============================================================

elif page == "Statistics":

    st.title("📊 Statistics")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        stats = [
            round_statistics(r)
            for r in rounds
        ]

        def average(key):

            return (
                sum(s[key] for s in stats)
                / len(stats)
            )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Average Score",
            f"{average('score'):.1f}"
        )

        col2.metric(
            "Average Putts",
            f"{average('putts'):.1f}"
        )

        col3.metric(
            "Average GIR",
            f"{average('gir'):.1f}%"
        )

        col4.metric(
            "Fairways",
            f"{average('fairways'):.1f}%"
        )

        st.divider()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Par 3 Average",
            f"{average('par3'):.2f}"
        )

        col2.metric(
            "Par 4 Average",
            f"{average('par4'):.2f}"
        )

        col3.metric(
            "Par 5 Average",
            f"{average('par5'):.2f}"
        )

        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Birdies",
            f"{average('birdies'):.1f}"
        )

        col2.metric(
            "Pars",
            f"{average('pars'):.1f}"
        )

        col3.metric(
            "Bogeys",
            f"{average('bogeys'):.1f}"
        )

        col4.metric(
            "Doubles+",
            f"{average('doubles'):.1f}"
        )


# ============================================================
# COURSE ANALYSIS
# ============================================================

elif page == "Course Analysis":

    st.title("⛳ Course Analysis")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        courses = {}

        for round_data in rounds:

            course = round_data["course"]

            if course not in courses:
                courses[course] = []

            courses[course].append(
                round_data
            )

        course_results = []

        for course, course_rounds in courses.items():

            stats = [
                round_statistics(r)
                for r in course_rounds
            ]

            course_results.append({
                "Course": course,
                "Rounds": len(course_rounds),
                "Average Score":
                    sum(s["score"] for s in stats)
                    / len(stats),
                "Best Score":
                    min(s["score"] for s in stats),
                "Average Putts":
                    sum(s["putts"] for s in stats)
                    / len(stats),
                "Average GIR":
                    sum(s["gir"] for s in stats)
                    / len(stats),
                "Average Fairways":
                    sum(s["fairways"] for s in stats)
                    / len(stats)
            })

        st.dataframe(
            pd.DataFrame(course_results),
            use_container_width=True
        )


# ============================================================
# HOLE ANALYSIS
# ============================================================

elif page == "Hole Analysis":

    st.title("🕳️ Hole Analysis")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        hole_results = []

        for hole in range(18):

            scores = []
            pars = []
            putts = []
            girs = []
            penalties = []

            for round_data in rounds:

                scores.append(
                    round_data["scores"][hole]
                )

                pars.append(
                    round_data["pars"][hole]
                )

                putts.append(
                    round_data["putts"][hole]
                )

                girs.append(
                    round_data["girs"][hole]
                )

                penalties.append(
                    round_data["penalties"][hole]
                )

            average_score = (
                sum(scores)
                / len(scores)
            )

            average_to_par = (
                sum(
                    scores[i] - pars[i]
                    for i in range(len(scores))
                )
                / len(scores)
            )

            average_putts = (
                sum(putts)
                / len(putts)
            )

            gir_percentage = (
                sum(girs)
                / len(girs)
                * 100
            )

            average_penalties = (
                sum(penalties)
                / len(penalties)
            )

            hole_results.append({
                "Hole": hole + 1,
                "Average Score":
                    round(average_score, 2),
                "To Par":
                    round(average_to_par, 2),
                "Putts":
                    round(average_putts, 2),
                "GIR":
                    f"{gir_percentage:.1f}%",
                "Penalties":
                    round(average_penalties, 2)
            })

        df = pd.DataFrame(hole_results)

        st.dataframe(
            df,
            use_container_width=True
        )

        hardest = sorted(
            hole_results,
            key=lambda x: x["To Par"],
            reverse=True
        )[:5]

        easiest = sorted(
            hole_results,
            key=lambda x: x["To Par"]
        )[:5]

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Hardest Holes")

            for hole in hardest:

                st.write(
                    f"Hole {hole['Hole']}: "
                    f"{hole['To Par']:+.2f}"
                )

        with col2:

            st.subheader("Easiest Holes")

            for hole in easiest:

                st.write(
                    f"Hole {hole['Hole']}: "
                    f"{hole['To Par']:+.2f}"
                )


# ============================================================
# GRAPHS
# ============================================================

elif page == "Graphs":

    st.title("📈 Graphs")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        stats = [
            round_statistics(r)
            for r in rounds
        ]

        round_numbers = list(
            range(1, len(rounds) + 1)
        )

        scores = [
            s["score"]
            for s in stats
        ]

        handicaps = [
            r["handicap"]
            for r in rounds
        ]

        putts = [
            s["putts"]
            for s in stats
        ]

        gir = [
            s["gir"]
            for s in stats
        ]

        fairways = [
            s["fairways"]
            for s in stats
        ]

        penalties = [
            s["penalties"]
            for s in stats
        ]

        graph_choice = st.selectbox(
            "Choose a graph",
            [
                "Score",
                "Handicap",
                "Putts",
                "GIR",
                "Fairways",
                "Penalties"
            ]
        )

        fig, ax = plt.subplots()

        if graph_choice == "Score":

            ax.plot(
                round_numbers,
                scores,
                marker="o"
            )

            ax.set_ylabel("Score")
            ax.set_title(
                "Score Over Time"
            )

        elif graph_choice == "Handicap":

            ax.plot(
                round_numbers,
                handicaps,
                marker="o"
            )

            ax.set_ylabel("Handicap")
            ax.set_title(
                "Handicap Over Time"
            )

        elif graph_choice == "Putts":

            ax.plot(
                round_numbers,
                putts,
                marker="o"
            )

            ax.set_ylabel("Putts")
            ax.set_title(
                "Putts Over Time"
            )

        elif graph_choice == "GIR":

            ax.plot(
                round_numbers,
                gir,
                marker="o"
            )

            ax.set_ylabel("GIR %")
            ax.set_title(
                "GIR Over Time"
            )

        elif graph_choice == "Fairways":

            ax.plot(
                round_numbers,
                fairways,
                marker="o"
            )

            ax.set_ylabel("Fairways %")
            ax.set_title(
                "Fairways Over Time"
            )

        elif graph_choice == "Penalties":

            ax.plot(
                round_numbers,
                penalties,
                marker="o"
            )

            ax.set_ylabel("Penalties")
            ax.set_title(
                "Penalties Over Time"
            )

        ax.set_xlabel("Round")

        st.pyplot(fig)


# ============================================================
# PERSONAL RECORDS
# ============================================================

elif page == "Personal Records":

    st.title("🏆 Personal Records")

    if not rounds:

        st.info("No rounds recorded.")

    else:

        stats = [
            round_statistics(r)
            for r in rounds
        ]

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Best Score",
                min(s["score"] for s in stats)
            )

            st.metric(
                "Best Score To Par",
                min(s["to_par"] for s in stats)
            )

            st.metric(
                "Fewest Putts",
                min(s["putts"] for s in stats)
            )

            st.metric(
                "Best GIR",
                f"{max(s['gir'] for s in stats):.1f}%"
            )

        with col2:

            st.metric(
                "Best Fairways",
                f"{max(s['fairways'] for s in stats):.1f}%"
            )

            st.metric(
                "Fewest Penalties",
                min(s["penalties"] for s in stats)
            )

            st.metric(
                "Most Birdies",
                max(s["birdies"] for s in stats)
            )


# ============================================================
# SEARCH
# ============================================================

elif page == "Search Rounds":

    st.title("🔎 Search Rounds")

    search = st.text_input(
        "Search by course, date, or score"
    )

    if search:

        results = []

        for round_data in rounds:

            stats = round_statistics(
                round_data
            )

            searchable = (
                f"{round_data['course']} "
                f"{round_data['date']} "
                f"{stats['score']}"
            ).lower()

            if search.lower() in searchable:

                results.append({
                    "Date":
                        round_data["date"],
                    "Course":
                        round_data["course"],
                    "Score":
                        stats["score"],
                    "To Par":
                        stats["to_par"],
                    "Putts":
                        stats["putts"],
                    "GIR":
                        f"{stats['gir']:.1f}%"
                })

        if results:

            st.dataframe(
                pd.DataFrame(results),
                use_container_width=True
            )

        else:

            st.warning(
                "No matching rounds found."
            )