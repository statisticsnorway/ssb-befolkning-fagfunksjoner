import pandas as pd

from src.ssb_befolkning_fagfunksjoner.demographics.birth_rates import foedselsrate, samlet_fruktbarhet

df_start = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2025/bosatte_p2025-01-01_v1.parquet")
df_end = pd.read_parquet("/buckets/produkt/bosatte/klargjorte-data/2025/bosatte_p2025-12-31_v1.parquet")
foedsler = pd.read_parquet("/buckets/produkt/foedte/klargjorte-data/2025/foedte_p2025_v1.parquet")

foedselsrate(df_start, df_end, foedsler, aldersgruppering=5)
samlet_fruktbarhet(df_start, df_end, foedsler, aldersgruppering=1)
