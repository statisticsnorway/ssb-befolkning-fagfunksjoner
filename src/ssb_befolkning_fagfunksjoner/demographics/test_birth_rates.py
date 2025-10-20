import pandas as pd
from ssb_befolkning_fagfunksjoner.demographics.birth_rates import BirthRates

# ------------------------------------------------------------------------
# Testing the functions
# ------------------------------------------------------------------------

birthrates = BirthRates(
    aldersgruppe_col="aldersgruppe",
    alder_col="alder",
    kjoenn_col="kjoenn",
    skala=1000,
    aldersgruppering=5,
    min_alder=15,
    max_alder=49,
    beregn_for_menn=False
)

df_start = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2024/bosatte_p2024-01-01.parquet")
df_slutt = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2024/bosatte_p2024-12-31.parquet")

# Hvordan funker _beregn_middelfolkemengde()

# Steg 1: prepp folketall data
df_start = birthrates._filtrer_og_lag_aldersgrupper(df=df_start)
df_slutt = birthrates._filtrer_og_lag_aldersgrupper(df=df_slutt)
df_start

# Steg 2: normalisere grupperingsvariabler
grupperingsvariabler_0 = None 
norm_0 = birthrates._normaliser_grupperingsvariabler(grupperingsvariabler_0)

grupperingsvariabler_1 = "komm_nr"
norm_1 = birthrates._normaliser_grupperingsvariabler(grupperingsvariabler_1)
norm_1

grupperingsvariabler_2 = ["sivilstand", "landkode"]
norm_2 = birthrates._normaliser_grupperingsvariabler(grupperingsvariabler_2)
norm_2


# Steg 3: validere at kolonnene finnes
birthrates._valider_grupperingsvariabler(df_start, norm_1, "df_start")
birthrates._valider_grupperingsvariabler(df_start, norm_2, "df_start")  # skal feile fordi landkode ikke finnes

# Steg 4: tell opp antall personer per gruppe
a = df_start.groupby(norm_1, dropna=False).size().rename("n_df_start")
a
b = df_slutt.groupby(norm_1, dropna=False).size().rename("n_df_slutt")
b

# Steg 5: beregn mfm
mfm = pd.concat([a, b], axis=1).fillna(0)
mfm["middelfolkemengde"] = (mfm["n_df_start"] + mfm["n_df_slutt"]) / 2
mfm.reset_index()

# I alt
mfm = birthrates._beregn_middelfolkemengde(
    df_start,
    df_slutt,
    grupperingsvariabler=[]
)
mfm