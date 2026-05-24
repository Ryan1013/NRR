import streamlit as st
import pandas as pd
import copy

st.set_page_config(layout="wide")

# ------------------------------
# Utility Functions
# ------------------------------

def overs_to_float(overs):
    whole = int(overs)
    balls = round((overs - whole) * 10)
    return whole + balls / 6


class Team:
    def __init__(self, name):
        self.name = name
        self.rs = 0
        self.of = 0
        self.rc = 0
        self.ob = 0
        self.points = 0

    def bat(self, runs, overs):
        self.rs += runs
        self.of += overs_to_float(overs)

    def bowl(self, runs, overs):
        self.rc += runs
        self.ob += overs_to_float(overs)

    def nrr(self):
        if self.of == 0 or self.ob == 0:
            return 0
        return (self.rs / self.of) - (self.rc / self.ob)


# ------------------------------
# TITLE
# ------------------------------

st.title("🏏 NRR Equation Solver")

# ------------------------------
# TEAM INPUT
# ------------------------------

st.header("1️⃣ Teams")

n = st.number_input("Number of Teams", 2, 10, 3)

team_names = []
for i in range(n):
    name = st.text_input(f"Team {i+1}", f"Team_{i+1}")
    team_names.append(name)

teams = {name: Team(name) for name in team_names}


# ------------------------------
# MATCH INPUT
# ------------------------------

st.header("2️⃣ Completed Matches")

m = st.number_input("Number of Matches", 0, 50, 2)

for i in range(m):
    st.subheader(f"Match {i+1}")

    col1, col2 = st.columns(2)

    with col1:
        t1 = st.selectbox("Batting First", team_names, key=f"t1_{i}")
        r1 = st.number_input("Runs", 0, 500, key=f"r1_{i}")
        o1 = st.number_input("Overs", 0.0, 50.0, key=f"o1_{i}")

    with col2:
        t2 = st.selectbox("Chasing", team_names, key=f"t2_{i}")
        r2 = st.number_input("Runs ", 0, 500, key=f"r2_{i}")
        o2 = st.number_input("Overs ", 0.0, 50.0, key=f"o2_{i}")

    if t1 != t2:
        teams[t1].bat(r1, o1)
        teams[t2].bowl(r1, o1)

        teams[t2].bat(r2, o2)
        teams[t1].bowl(r2, o2)

        if r1 > r2:
            teams[t1].points += 2
        elif r2 > r1:
            teams[t2].points += 2


# ------------------------------
# TABLE
# ------------------------------

st.header("📊 Current Table")

table = []
for t in teams.values():
    table.append([t.name, t.points, round(t.nrr(), 4)])

df = pd.DataFrame(table, columns=["Team", "Points", "NRR"])
df = df.sort_values(["Points", "NRR"], ascending=False)

st.dataframe(df, use_container_width=True)


# ------------------------------
# FINAL MATCH
# ------------------------------

st.header("3️⃣ Final Match Scenario")

team_bat = st.selectbox(
    "Batting First Team",
    team_names
)

available_chasers = [
    team
    for team in team_names
    if team != team_bat
]

team_chase = st.selectbox(
    "Chasing Team",
    available_chasers
)

evaluated_team = st.selectbox(
    "Team Being Evaluated",
    team_names
)
target_pos = st.number_input("Target Position", 1, n, 1)

first_runs = st.number_input("First Innings Runs", 0, 500, 150)
first_overs = st.number_input("First Innings Overs", 0.0, 50.0, 20.0)


# ------------------------------
# SIMULATION
# ------------------------------

def simulate_defend(win_margin):

    sim = copy.deepcopy(teams)

    sim[team_bat].bat(first_runs, first_overs)
    sim[team_chase].bowl(first_runs, first_overs)

    chase_runs = first_runs - win_margin
    chase_overs = first_overs

    sim[team_chase].bat(chase_runs, chase_overs)
    sim[team_bat].bowl(chase_runs, chase_overs)

    sim[team_bat].points += 2

    ranking = sorted(
        sim.values(),
        key=lambda x: (x.points, x.nrr()),
        reverse=True
    )

    positions = {
        team.name: idx + 1
        for idx, team in enumerate(ranking)
    }

    table = []

    for team in ranking:
        table.append([
            team.name,
            team.points,
            round(team.nrr(), 4)
        ])

    table_df = pd.DataFrame(
        table,
        columns=["Team", "Points", "NRR"]
    )

    return positions, table_df


def simulate_chase(chase_overs):

    sim = copy.deepcopy(teams)

    sim[team_bat].bat(first_runs, first_overs)
    sim[team_chase].bowl(first_runs, first_overs)

    chase_runs = first_runs + 1

    sim[team_chase].bat(chase_runs, chase_overs)
    sim[team_bat].bowl(chase_runs, chase_overs)

    sim[team_chase].points += 2

    ranking = sorted(
        sim.values(),
        key=lambda x: (x.points, x.nrr()),
        reverse=True
    )

    positions = {
        team.name: idx + 1
        for idx, team in enumerate(ranking)
    }

    table = []

    for team in ranking:
        table.append([
            team.name,
            team.points,
            round(team.nrr(), 4)
        ])

    table_df = pd.DataFrame(
        table,
        columns=["Team", "Points", "NRR"]
    )

    return positions, table_df


# ------------------------------
# SOLVER BUTTON
# ------------------------------

if st.button("🚀 Calculate"):

    is_playing = (
        evaluated_team in
        [team_bat, team_chase]
    )

    chase_solutions = []
    defend_solutions = []

    for balls in range(
        1,
        int(first_overs * 6) + 1
    ):

        overs = (
            balls // 6
            + (balls % 6) / 10
        )

        positions, table_df = simulate_chase(
            overs
        )

        if (
            positions[evaluated_team]
            <= target_pos
        ):

            chase_solutions.append({
                "overs": overs,
                "table": table_df
            })

    for margin in range(
        1,
        int(first_runs)
    ):

        positions, table_df = simulate_defend(
            margin
        )

        if (
            positions[evaluated_team]
            <= target_pos
        ):

            defend_solutions.append({
                "margin": margin,
                "table": table_df
            })

    st.header("📈 Results")

    # ------------------
    # Chase scenario
    # ------------------

    if chase_solutions:

        best_chase = max(
            chase_solutions,
            key=lambda x: x["overs"]
        )

        if is_playing:

            st.success(
                f"{evaluated_team} qualifies "
                f"if they chase "
                f"{first_runs + 1} in "
                f"{best_chase['overs']:.1f} "
                f"overs or fewer."
            )

        else:

            st.success(
                f"For {evaluated_team} "
                f"to finish Top "
                f"{target_pos}, "
                f"{team_chase} must not "
                f"chase faster than "
                f"{best_chase['overs']:.1f} "
                f"overs."
            )

        st.subheader(
            "Table at Chase Threshold"
        )

        st.dataframe(
            best_chase["table"],
            use_container_width=True
        )

    else:

        st.error(
            "No chase qualification scenario."
        )

    # ------------------
    # Defend scenario
    # ------------------

    if defend_solutions:

        best_defend = min(
            defend_solutions,
            key=lambda x: x["margin"]
        )

        if is_playing:

            st.success(
                f"{evaluated_team} qualifies "
                f"if they win by at least "
                f"{best_defend['margin']} runs."
            )

        else:

            st.success(
                f"For {evaluated_team} "
                f"to finish Top "
                f"{target_pos}, "
                f"{team_bat} must win "
                f"by at least "
                f"{best_defend['margin']} runs."
            )

        st.subheader(
            "Table at Defending Threshold"
        )

        st.dataframe(
            best_defend["table"],
            use_container_width=True
        )

    else:

        st.error(
            "No defending qualification scenario."
        )
