import pandas as pd
from services.postgres_conn import get_pg_conn

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import numpy as np

load_dotenv()  # carga .env al entorno

PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")

def get_connection():
    DATABASE_URL = (
        f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}"
        f"@{PGHOST}:{PGPORT}/{PGDATABASE}"
    )

    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,   # evita conexiones muertas
        echo=False            # True si quieres ver SQL
    )
    return engine

def get_data(engine, asset: str = "BTC"):
    query = """
        SELECT
        main.run_main_id,
        main.asset,
        main.ran_at_utc,
        main.spot_price  AS spot_run,
        det.detail_id,
        det.expiry_date,
        det.days_to_expiry,
        det.future_price,
        det.open_interest,
        det.spot_price   AS spot_detail,
        det.premium_pct,
        det.annualized_pct,
        det.curve,
        det.instrument_name
        FROM cryptodata.run_main AS main
        JOIN cryptodata.run_details AS det
        ON main.run_main_id = det.run_main_id
        WHERE main.asset = :asset;
    """
    return pd.read_sql(text(query), engine, params={"asset": asset})

    




def get_days_to_expiry(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.copy()

    # distance to anchor
    df["dist_270"] = (df["days_to_expiry"] - 270).abs()

    # anchor per run
    df["anchor_rank"] = (
        df.sort_values(["ran_at_utc", "dist_270", "days_to_expiry"])
          .groupby("ran_at_utc")
          .cumcount() + 1
    )

    anchors = (
        df[df["anchor_rank"] == 1]
        [["ran_at_utc", "days_to_expiry", "spot_run"]]
        .rename(columns={"days_to_expiry": "t_270"})
    )

    # attach anchor
    df = df.merge(
        anchors[["ran_at_utc", "t_270"]],
        on="ran_at_utc",
        how="left"
    )

    # below / above
    below = df[df["days_to_expiry"] < df["t_270"]].copy()
    above = df[df["days_to_expiry"] > df["t_270"]].copy()

    below["below_rank"] = (
        below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    above["above_rank"] = (
        above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    def pick(df, rank_col, rank, name):
        return (
            df[df[rank_col] == rank]
            .set_index("ran_at_utc")["days_to_expiry"]
            .rename(name)
        )

    result = anchors.set_index("ran_at_utc")[["spot_run", "t_270"]]

    result = result.join([
        pick(below, "below_rank", 6, "t_1"),
        pick(below, "below_rank", 5, "t_7"),
        pick(below, "below_rank", 4, "t_30"),
        pick(below, "below_rank", 3, "t_60"),
        pick(below, "below_rank", 2, "t_90"),
        pick(below, "below_rank", 1, "t_180"),
        pick(above, "above_rank", 1, "t_360"),
    ])

    result = result.reset_index()
    
    # Reorder columns: t_270 between t_180 and t_360
    result = result[["ran_at_utc", "spot_run", "t_1", "t_7", "t_30", "t_60", "t_90", "t_180", "t_270", "t_360"]]
    
    # Round numeric columns to 2 decimal places
    numeric_cols = ["spot_run", "t_1", "t_7", "t_30", "t_60", "t_90", "t_180", "t_270", "t_360"]
    for col in numeric_cols:
        if col in result.columns:
            result[col] = result[col].round(2)
    
    return result


def get_annualized_forward_premiums(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns annualized forward premiums grouped by date, similar to 
    annualized_forward_premiums_grouped_by_date.sql
    """
    df = df.copy()

    # distance to anchor
    df["dist_270"] = (df["days_to_expiry"] - 270).abs()

    # anchor per run
    df["anchor_rank"] = (
        df.sort_values(["ran_at_utc", "dist_270", "days_to_expiry"])
          .groupby("ran_at_utc")
          .cumcount() + 1
    )

    anchors = (
        df[df["anchor_rank"] == 1]
        [["ran_at_utc", "days_to_expiry"]]
        .rename(columns={"days_to_expiry": "anchor_days_to_expiry"})
    )

    # attach anchor to all rows
    df = df.merge(
        anchors[["ran_at_utc", "anchor_days_to_expiry"]],
        on="ran_at_utc",
        how="left"
    )

    # below / above anchor
    below = df[df["days_to_expiry"] < df["anchor_days_to_expiry"]].copy()
    above = df[df["days_to_expiry"] > df["anchor_days_to_expiry"]].copy()

    # rank below anchor (descending by days_to_expiry)
    below["below_rank"] = (
        below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    # rank above anchor (ascending by days_to_expiry)
    above["above_rank"] = (
        above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    def pick_premium(df, rank_col, rank, name):
        """Pick annualized_pct for a specific rank"""
        return (
            df[df[rank_col] == rank]
            .set_index("ran_at_utc")["annualized_pct"]
            .rename(name)
        )

    # Get anchor premium (prem270) - use anchor_rank == 1
    anchor_premiums = (
        df[df["anchor_rank"] == 1]
        .set_index("ran_at_utc")["annualized_pct"]
        .rename("prem270")
    )

    # Start with anchor dates
    result = anchors.set_index("ran_at_utc")[[]]  # Empty dataframe with just index

    # Join all premiums
    result = result.join([
        pick_premium(below, "below_rank", 6, "prem1"),
        pick_premium(below, "below_rank", 5, "prem7"),
        pick_premium(below, "below_rank", 4, "prem30"),
        pick_premium(below, "below_rank", 3, "prem60"),
        pick_premium(below, "below_rank", 2, "prem90"),
        pick_premium(below, "below_rank", 1, "prem180"),
        anchor_premiums,
        pick_premium(above, "above_rank", 1, "prem360"),
    ])

    result = result.reset_index()
    
    # Reorder columns: prem270 between prem180 and prem360
    result = result[["ran_at_utc", "prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]]
    
    # Round numeric columns to 2 decimal places
    numeric_cols = ["prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]
    for col in numeric_cols:
        if col in result.columns:
            result[col] = result[col].round(2)
    
    return result


def get_forward_premiums_vs_sample_median(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns forward premiums vs sample median, similar to 
    forward_premiums_vs_sample_median.sql
    Calculates premiums, then subtracts the median of each premium across all dates.
    """
    df = df.copy()

    # distance to anchor
    df["dist_270"] = (df["days_to_expiry"] - 270).abs()

    # anchor per run
    df["anchor_rank"] = (
        df.sort_values(["ran_at_utc", "dist_270", "days_to_expiry"])
          .groupby("ran_at_utc")
          .cumcount() + 1
    )

    anchors = (
        df[df["anchor_rank"] == 1]
        [["ran_at_utc", "days_to_expiry"]]
        .rename(columns={"days_to_expiry": "anchor_days_to_expiry"})
    )

    # attach anchor to all rows
    df = df.merge(
        anchors[["ran_at_utc", "anchor_days_to_expiry"]],
        on="ran_at_utc",
        how="left"
    )

    # below / above anchor
    below = df[df["days_to_expiry"] < df["anchor_days_to_expiry"]].copy()
    above = df[df["days_to_expiry"] > df["anchor_days_to_expiry"]].copy()

    # rank below anchor (descending by days_to_expiry)
    below["below_rank"] = (
        below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    # rank above anchor (ascending by days_to_expiry)
    above["above_rank"] = (
        above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True])
             .groupby("ran_at_utc")
             .cumcount() + 1
    )

    def pick_premium(df, rank_col, rank, name):
        """Pick annualized_pct for a specific rank"""
        return (
            df[df[rank_col] == rank]
            .set_index("ran_at_utc")["annualized_pct"]
            .rename(name)
        )

    # Get anchor premium (prem7)
    anchor_premiums = (
        df[df["anchor_rank"] == 1]
        .set_index("ran_at_utc")["annualized_pct"]
        .rename("prem7")
    )

    # Start with anchor dates
    result = anchors.set_index("ran_at_utc")[[]]  # Empty dataframe with just index

    # Join all premiums (prem1-8 as in SQL)
    result = result.join([
        pick_premium(below, "below_rank", 6, "prem1"),
        pick_premium(below, "below_rank", 5, "prem2"),
        pick_premium(below, "below_rank", 4, "prem3"),
        pick_premium(below, "below_rank", 3, "prem4"),
        pick_premium(below, "below_rank", 2, "prem5"),
        pick_premium(below, "below_rank", 1, "prem6"),
        anchor_premiums,  # prem7
        pick_premium(above, "above_rank", 1, "prem8"),
    ])

    result = result.reset_index()

    # Calculate medians for each premium column (percentile_cont(0.5) in SQL)
    medians = {
        'med_prem1': result['prem1'].median(),
        'med_prem2': result['prem2'].median(),
        'med_prem3': result['prem3'].median(),
        'med_prem4': result['prem4'].median(),
        'med_prem5': result['prem5'].median(),
        'med_prem6': result['prem6'].median(),
        'med_prem7': result['prem7'].median(),
        'med_prem8': result['prem8'].median(),
    }

    # Subtract medians from each premium (as in SQL)
    # Map: prem1->prem1, prem2->prem7, prem3->prem30, prem4->prem60, 
    #      prem5->prem90, prem6->prem180, prem7->prem270, prem8->prem360
    # Save original prem7 before overwriting
    original_prem7 = result['prem7'].copy()
    
    result['prem1'] = result['prem1'] - medians['med_prem1']
    result['prem7'] = result['prem2'] - medians['med_prem2']
    result['prem30'] = result['prem3'] - medians['med_prem3']
    result['prem60'] = result['prem4'] - medians['med_prem4']
    result['prem90'] = result['prem5'] - medians['med_prem5']
    result['prem180'] = result['prem6'] - medians['med_prem6']
    result['prem270'] = original_prem7 - medians['med_prem7']
    result['prem360'] = result['prem8'] - medians['med_prem8']

    # Select and reorder columns (matching SQL output)
    result = result[["ran_at_utc", "prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]]
    
    # Round numeric columns to 2 decimal places
    numeric_cols = ["prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]
    for col in numeric_cols:
        if col in result.columns:
            result[col] = result[col].round(2)
    
    return result


def get_spot_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns spot price per date, similar to Excel 'spot' column.
    """
    result = (
        df.groupby("ran_at_utc")["spot_run"]
        .first()
        .reset_index()
        .rename(columns={"spot_run": "spot"})
    )
    
    # Round to 2 decimal places
    result["spot"] = result["spot"].round(2)
    
    return result

import numpy as np
import pandas as pd

def get_forward_price_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Matches Excel:
      dASSET.F1 = LN(price[t+1] / price[t])
      dASSET.F5 = LN(price[t+5] / price[t])
    (Forward-looking log returns, blank if target cell is blank.)
    """
    df = df.copy()

    # One row per timestamp (if df has multiple contracts per ran_at_utc)
    # If you already have 1 row per ran_at_utc, this just keeps it stable.
    df = df.sort_values("ran_at_utc")
    df = df.drop_duplicates(subset=["ran_at_utc"], keep="first")

    asset = df["asset"].iloc[0] if "asset" in df.columns and len(df) else "BTC"
    f1_col = f"d{asset}.F1"
    f5_col = f"d{asset}.F5"

    price = df["spot_run"].astype(float)

    # Excel IF(target="";"";LN(target/current))
    df[f1_col] = np.where(
        price.shift(-1).isna(),
        np.nan,
        np.log(price.shift(-1) / price)
    )

    df[f5_col] = np.where(
        price.shift(-5).isna(),
        np.nan,
        np.log(price.shift(-5) / price)
    )

    return df[["ran_at_utc", f1_col, f5_col]]


def get_cross_correlations_f1(df: pd.DataFrame, window: int = None, min_periods: int = 4) -> pd.DataFrame:
    """
    Cross correlations between annualized forward premiums (prem*) and dASSET.F1.
    - If window is None: expanding correlation up to each date (row i uses rows 0..i).
    - If window is specified: rolling correlation over that window (row i uses last 'window' rows).
    - Starts output only from the 4th row by default (min_periods=4).
    """
    premiums_df = get_annualized_forward_premiums(df)
    changes_df  = get_forward_price_changes(df)

    asset = df["asset"].iloc[0] 
    f1_col = f"d{asset}.F1"

    merged = premiums_df.merge(changes_df, on="ran_at_utc", how="inner")
    merged = merged.sort_values("ran_at_utc").reset_index(drop=True)

    premium_cols = ["prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]
    result = merged[["ran_at_utc"]].copy()

    for col in premium_cols:
        if col not in merged.columns or f1_col not in merged.columns:
            continue

        correlations = [None] * len(merged)

        for i in range(len(merged)):
            # Regla "a partir de la 4ta fila"
            if i < (min_periods - 1):
                correlations[i] = None
                continue

            if window is None:
                window_data = merged.iloc[:i+1][[col, f1_col]].dropna()
            else:
                start_idx = max(0, i - window + 1)
                window_data = merged.iloc[start_idx:i+1][[col, f1_col]].dropna()

            # Requiere al menos 4 pares válidos (o min_periods)
            if len(window_data) >= min_periods:
                corr = window_data[col].corr(window_data[f1_col])
                correlations[i] = None if pd.isna(corr) else corr
            else:
                correlations[i] = None

        result[col] = correlations

    # Ojo: redondear a 2 decimales puede matar señal (log-returns suelen ser pequeños)
    for col in premium_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").round(2)

    return result



def get_cross_correlations_f5(
    df: pd.DataFrame,
    window: int = None,
    min_periods: int = 3,
    debug: bool = False
) -> pd.DataFrame:
    """
    Cross correlations between annualized forward premiums (prem*)
    and dASSET.F5 with full diagnostics.
    """

    if debug:
        print("\n====================")
        print("DEBUG: get_cross_correlations_f5 START")
        print("====================")

    premiums_df = get_annualized_forward_premiums(df)
    changes_df  = get_forward_price_changes(df)

    asset = df["asset"].iloc[0] 
    f5_col = f"d{asset}.F5"

    if debug:
        print("\n[DEBUG] Columns in changes_df:")
        print(changes_df.columns.tolist())
        print("[DEBUG] Expected F5 column:", f5_col)

    merged = premiums_df.merge(changes_df, on="ran_at_utc", how="inner")
    merged = merged.sort_values("ran_at_utc").reset_index(drop=True)

    if debug:
        print("\n[DEBUG] merged.shape:", merged.shape)
        print("[DEBUG] merged.head():")
        print(merged.head(10))

        if f5_col in merged.columns:
            print("\n[DEBUG] dBTC.F5 non-null count:",
                  merged[f5_col].notna().sum(),
                  "out of", len(merged))
        else:
            print("\n[DEBUG] ❌ dBTC.F5 column NOT FOUND in merged")

    premium_cols = [
        "prem1", "prem7", "prem30", "prem60",
        "prem90", "prem180", "prem270", "prem360"
    ]

    result = merged[["ran_at_utc"]].copy()

    for col in premium_cols:
        if col not in merged.columns or f5_col not in merged.columns:
            if debug:
                print(f"\n[DEBUG] Skipping {col} (missing column)")
            continue

        if debug:
            pair_count = merged[[col, f5_col]].dropna().shape[0]
            print(f"\n[DEBUG] {col} vs {f5_col}")
            print(f"        valid (non-NaN) pairs: {pair_count}")

        correlations = np.full(len(merged), np.nan)

        for i in range(len(merged)):
            if i < (min_periods - 1):
                if debug and i == min_periods - 2:
                    print(f"        first possible index = {min_periods - 1}")
                continue

            if window is None:
                window_data = merged.iloc[:i+1][[col, f5_col]].dropna()
                window_type = "EXPANDING"
            else:
                start_idx = max(0, i - window + 1)
                window_data = merged.iloc[start_idx:i+1][[col, f5_col]].dropna()
                window_type = f"ROLLING({window})"

            if debug and i < min_periods + 2:
                print(
                    f"        row {i}: {window_type}, "
                    f"rows used={len(window_data)}"
                )

            if len(window_data) >= min_periods:
                corr = window_data[col].corr(window_data[f5_col])
                if not pd.isna(corr):
                    correlations[i] = corr
                    if debug and i < min_periods + 2:
                        print(f"            ✔ corr={corr:.4f}")
                else:
                    if debug and i < min_periods + 2:
                        print("            ✖ corr is NaN")
            else:
                if debug and i < min_periods + 2:
                    print("            ✖ not enough valid data")

        result[col] = correlations

    # Final rounding (safe)
    for col in premium_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").round(2)

    if debug:
        print("\n====================")
        print("DEBUG: get_cross_correlations_f5 END")
        print("====================\n")

    return result


def join_all_analysis_excel_like(
    df_raw: pd.DataFrame,
    corr_window: int | None = None,
    add_separators: bool = True
) -> pd.DataFrame:
    """
    Builds ONE master dataframe (like your Excel) by joining:
      - spot
      - days_to_expiry buckets (t_*)
      - annualized premiums (prem*)
      - premiums vs sample median (dev*)
      - forward price changes (dASSET.F1 / dASSET.F5)
      - cross correlations vs F1 (corrF1_*)
      - cross correlations vs F5 (corrF5_*)
    """

    df_raw = df_raw.copy()
    df_raw["ran_at_utc"] = pd.to_datetime(df_raw["ran_at_utc"])

    # Base index (all dates)
    base = (
        pd.DataFrame({"ran_at_utc": pd.Series(df_raw["ran_at_utc"].unique())})
        .sort_values("ran_at_utc")
        .reset_index(drop=True)
    )

    # --- compute pieces ---
    spot = get_spot_price(df_raw)  # ran_at_utc, spot

    days = get_days_to_expiry(df_raw)  # ran_at_utc, spot_run, t_1..t_360
    # avoid duplicate spot columns (we already have spot)
    if "spot_run" in days.columns:
        days = days.drop(columns=["spot_run"])

    prem = get_annualized_forward_premiums(df_raw)  # ran_at_utc, prem1..prem360
    prem = prem.rename(columns={c: f"prem_{c}" for c in prem.columns if c != "ran_at_utc"})
    # gives prem_prem1, prem_prem7... so fix to prem_1 etc:
    prem = prem.rename(columns={
        "prem_prem1": "prem_1",
        "prem_prem7": "prem_7",
        "prem_prem30": "prem_30",
        "prem_prem60": "prem_60",
        "prem_prem90": "prem_90",
        "prem_prem180": "prem_180",
        "prem_prem270": "prem_270",
        "prem_prem360": "prem_360",
    })

    dev = get_forward_premiums_vs_sample_median(df_raw)  # ran_at_utc, prem1,prem7,prem30...
    dev = dev.rename(columns={c: f"dev_{c}" for c in dev.columns if c != "ran_at_utc"})
    dev = dev.rename(columns={
        "dev_prem1": "dev_1",
        "dev_prem7": "dev_7",
        "dev_prem30": "dev_30",
        "dev_prem60": "dev_60",
        "dev_prem90": "dev_90",
        "dev_prem180": "dev_180",
        "dev_prem270": "dev_270",
        "dev_prem360": "dev_360",
    })

    changes = get_forward_price_changes(df_raw)  # ran_at_utc, dASSET.F1, dASSET.F5

    corr_f1 = get_cross_correlations_f1(df_raw, window=corr_window)  # ran_at_utc, prem1..prem360
    corr_f1 = corr_f1.rename(columns={c: f"corrF1_{c}" for c in corr_f1.columns if c != "ran_at_utc"})
    corr_f1 = corr_f1.rename(columns={
        "corrF1_prem1": "corrF1_1",
        "corrF1_prem7": "corrF1_7",
        "corrF1_prem30": "corrF1_30",
        "corrF1_prem60": "corrF1_60",
        "corrF1_prem90": "corrF1_90",
        "corrF1_prem180": "corrF1_180",
        "corrF1_prem270": "corrF1_270",
        "corrF1_prem360": "corrF1_360",
    })

    corr_f5 = get_cross_correlations_f5(df_raw, window=corr_window)
    corr_f5 = corr_f5.rename(columns={c: f"corrF5_{c}" for c in corr_f5.columns if c != "ran_at_utc"})
    corr_f5 = corr_f5.rename(columns={
        "corrF5_prem1": "corrF5_1",
        "corrF5_prem7": "corrF5_7",
        "corrF5_prem30": "corrF5_30",
        "corrF5_prem60": "corrF5_60",
        "corrF5_prem90": "corrF5_90",
        "corrF5_prem180": "corrF5_180",
        "corrF5_prem270": "corrF5_270",
        "corrF5_prem360": "corrF5_360",
    })

    # --- merge all (outer to keep all dates) ---
    master = base.merge(spot, on="ran_at_utc", how="left")
    master = master.merge(days, on="ran_at_utc", how="left")
    master = master.merge(prem, on="ran_at_utc", how="left")
    master = master.merge(dev, on="ran_at_utc", how="left")
    master = master.merge(changes, on="ran_at_utc", how="left")
    master = master.merge(corr_f1, on="ran_at_utc", how="left")
    master = master.merge(corr_f5, on="ran_at_utc", how="left")

    # --- optional blank separator columns like Excel ---
    if add_separators:
        # build a nice column order + separators
        cols = ["ran_at_utc", "spot"]

        days_cols = [c for c in ["t_1","t_7","t_30","t_60","t_90","t_180","t_270","t_360"] if c in master.columns]
        prem_cols = [c for c in ["prem_1","prem_7","prem_30","prem_60","prem_90","prem_180","prem_270","prem_360"] if c in master.columns]
        dev_cols  = [c for c in ["dev_1","dev_7","dev_30","dev_60","dev_90","dev_180","dev_270","dev_360"] if c in master.columns]
        chg_cols  = [c for c in master.columns if c.startswith("d") and ".F" in c]  # dBTC.F1, dBTC.F5
        c1_cols   = [c for c in ["corrF1_1","corrF1_7","corrF1_30","corrF1_60","corrF1_90","corrF1_180","corrF1_270","corrF1_360"] if c in master.columns]
        c5_cols   = [c for c in ["corrF5_1","corrF5_7","corrF5_30","corrF5_60","corrF5_90","corrF5_180","corrF5_270","corrF5_360"] if c in master.columns]

        # create separators (empty strings)
        for sep in ["sep_days", "sep_prem", "sep_dev", "sep_chg", "sep_c1", "sep_c5"]:
            master[sep] = ""

        cols = (
            ["ran_at_utc", "spot"]
            + ["sep_days"] + days_cols
            + ["sep_prem"] + prem_cols
            + ["sep_dev"]  + dev_cols
            + ["sep_chg"]  + chg_cols
            + ["sep_c1"]   + c1_cols
            + ["sep_c5"]   + c5_cols
        )

        # keep any extra columns at the end (just in case)
        extras = [c for c in master.columns if c not in cols]
        master = master[cols + extras]

    return master.sort_values("ran_at_utc").reset_index(drop=True)


def main():
    engine = get_connection()

    assets = ["BTC", "ETH"]

    # One workbook, one sheet per asset
    with pd.ExcelWriter("master_analysis.xlsx", engine="openpyxl") as writer:
        for asset in assets:
            df = get_data(engine, asset=asset)

            master = join_all_analysis_excel_like(df, corr_window=None, add_separators=True)

            # Excel doesn't like tz-aware datetimes
            master["ran_at_utc"] = pd.to_datetime(master["ran_at_utc"], utc=True).dt.tz_convert(None)

            # Write each asset to its own sheet (pestaña)
            master.to_excel(writer, sheet_name=asset, index=False)

            print(f"Wrote sheet: {asset} | rows={len(master)}")

    print("Saved: master_analysis.xlsx")

main()

