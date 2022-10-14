import pandas as pd


def get_experiment_df(file):
    df = pd.read_excel(file)

    # get rid of vpvC mutants. They are not interesting
    inds = df["Strains"].str.contains("vpvC")
    df = df.loc[~inds, :]

    df.index = df["Date"].str.cat(df["Well"], sep="-")
    df.index.name = "experiment_id"

    # rename the different used deltas
    correct_delta = b"\xe2\x88\x86".decode("UTF-8")
    wrong_delta = b"\xce\x94".decode("UTF-8")

    df.loc[:, "Strains"] = df.loc[:, "Strains"].str.replace(wrong_delta, correct_delta)

    # nicer ratios
    df.loc[df["Ratio"] == "1 to 1", "ratio"] = "1/1"
    df.loc[df["Ratio"] == "1 to 2", "ratio"] = "1/2"
    df.loc[df["Ratio"] == "3 to 4", "ratio"] = "3/4"
    df.loc[df["Ratio"] == "1 to 4", "ratio"] = "1/4"

    # more curation
    organisms_mutations = df["Strains"].str.strip().str.split(" ", expand=True)

    all_mutations = []

    for i in range(1, organisms_mutations.columns.stop):
        inds = ~organisms_mutations[i].isnull()
        all_mutations.extend(set(organisms_mutations.loc[inds, i]))

    all_mutations = list(set(all_mutations))

    species = organisms_mutations[0].str.split("+", expand=True)
    df["species1"] = species[1]
    df["species2"] = species[0]

    inds = df["species1"].isnull()
    df.loc[inds, "species1"] = df.loc[inds, "species2"]
    df.loc[inds, "species2"] = "No 2nd species"

    inds = df["species2"] == "Va"
    df.loc[inds, "species2"] = "VA"

    # nice mutation names
    df["nice mutations"] = ""
    df["add mutations"] = " "

    df["nice mutations2"] = ""
    df["add mutations2"] = " "
    df["nice mutations2 vert"] = ""

    df["nice mutations3"] = ""
    df["add mutations3"] = " "

    df["nice mutations4"] = ""

    df["num mutations"] = 0
    for m in sorted(all_mutations):
        inds = df["Strains"].str.contains(m)

        df.loc[inds, "num mutations"] += 1

        df.loc[inds, "add mutations"] = "x"
        df.loc[~inds, "add mutations"] = " "

        df.loc[inds, "add mutations2"] = m
        df.loc[~inds, "add mutations2"] = " " * len(m)

        df.loc[inds, "add mutations3"] = "1"
        df.loc[~inds, "add mutations3"] = "0"

        df["nice mutations"] = df["nice mutations"].str.cat(
            df["add mutations"], sep=" "
        )
        df["nice mutations2"] = df["nice mutations2"].str.cat(
            df["add mutations2"], sep=" "
        )
        df["nice mutations2 vert"] = df["nice mutations2 vert"].str.cat(
            df["add mutations2"], sep="\n"
        )
        df["nice mutations3"] = df["nice mutations3"].str.cat(
            df["add mutations3"], sep=""
        )

        df.loc[inds, "nice mutations4"] = df.loc[inds, "nice mutations4"].str.cat(
            df.loc[inds, "add mutations2"], sep=" "
        )

    inds = df["nice mutations4"] == ""
    df.loc[inds, "nice mutations4"] = "WT"

    df["mutations"] = df["nice mutations4"].str.cat(df["nice mutations"], sep=" | ")
    df["mutations2"] = df["nice mutations"].str.cat(df["nice mutations4"], sep=" | ")

    df["order mutations"] = df["nice mutations3"].astype(int)
    df = df.sort_values(
        ["num mutations", "order mutations"], axis=0, ascending=[True, False]
    )

    return df
