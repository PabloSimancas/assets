import pandas as pd
import numpy as np
from sqlalchemy import text
from src.infrastructure.database.session import engine

class AnalysisService:
    @staticmethod
    def get_raw_data(symbol: str) -> pd.DataFrame:
        print(f"DEBUG: Fetching raw data for {symbol}")
        # print db url hiddenly
        import os
        print(f"DEBUG: DB URL starts with {os.getenv('DATABASE_URL', 'Not Set')[:10]}")
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
            FROM crypto_forwards.run_main AS main
            JOIN crypto_forwards.run_details AS det
            ON main.run_main_id = det.run_main_id
            WHERE main.asset = :asset
            ORDER BY main.ran_at_utc ASC;
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), {"asset": symbol})
                # Convert to DataFrame
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            print(f"DEBUG: Fetched {len(df)} rows")
            if not df.empty:
                # Ensure ran_at_utc is datetime
                df["ran_at_utc"] = pd.to_datetime(df["ran_at_utc"])
                
                # Convert Decimals to float (postgres returns Decimal for NUMERIC)
                numeric_cols = ["spot_run", "future_price", "open_interest", "spot_detail", "premium_pct", "annualized_pct"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].astype(float)
            
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_days_to_expiry(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        df = df.copy()
        
        # logic from presenter
        df["dist_270"] = (df["days_to_expiry"] - 270).abs()
        
        # anchor per run (closest to 270 days)
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

        df = df.merge(anchors[["ran_at_utc", "t_270"]], on="ran_at_utc", how="left")

        below = df[df["days_to_expiry"] < df["t_270"]].copy()
        above = df[df["days_to_expiry"] > df["t_270"]].copy()

        below["below_rank"] = below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False]).groupby("ran_at_utc").cumcount() + 1
        above["above_rank"] = above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True]).groupby("ran_at_utc").cumcount() + 1

        def pick(df_sub, rank_col, rank, name):
            return df_sub[df_sub[rank_col] == rank].set_index("ran_at_utc")["days_to_expiry"].rename(name)

        result = anchors.set_index("ran_at_utc")[["t_270"]]
        
        # Merge picked columns
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
        return result.sort_values("ran_at_utc")

    @staticmethod
    def get_annualized_forward_premiums(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        df = df.copy()

        df["dist_270"] = (df["days_to_expiry"] - 270).abs()
        df["anchor_rank"] = df.sort_values(["ran_at_utc", "dist_270", "days_to_expiry"]).groupby("ran_at_utc").cumcount() + 1

        anchors = df[df["anchor_rank"] == 1][["ran_at_utc", "days_to_expiry"]].rename(columns={"days_to_expiry": "anchor_days_to_expiry"})
        df = df.merge(anchors, on="ran_at_utc", how="left")

        below = df[df["days_to_expiry"] < df["anchor_days_to_expiry"]].copy()
        above = df[df["days_to_expiry"] > df["anchor_days_to_expiry"]].copy()

        below["below_rank"] = below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False]).groupby("ran_at_utc").cumcount() + 1
        above["above_rank"] = above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True]).groupby("ran_at_utc").cumcount() + 1

        def pick_premium(df_sub, rank_col, rank, name):
            return df_sub[df_sub[rank_col] == rank].set_index("ran_at_utc")["annualized_pct"].rename(name)

        anchor_premiums = df[df["anchor_rank"] == 1].set_index("ran_at_utc")["annualized_pct"].rename("prem270")

        result = anchors.set_index("ran_at_utc")[[]]
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

        return result.reset_index()

    @staticmethod
    def get_forward_premiums_vs_sample_median(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        # First get the standard premiums
        premiums = AnalysisService.get_annualized_forward_premiums(df)
        if premiums.empty: return pd.DataFrame()

        result = premiums.copy()
        
        # Calculate medians manually as per logic
        median_cols = ["prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]
        medians = {}

        for col in median_cols:
            if col in result.columns:
                medians[col] = result[col].median()
            else:
                medians[col] = 0 # Safety

        # Calculate deviations (renaming logic from presenter)
        # dev_1 = prem1 - median(prem1)
        if "prem1" in result.columns: result["dev_1"] = result["prem1"] - medians["prem1"]
        # dev_7 = prem2 (SQL logic was weirdly shifting, but presenter logic: result['prem7'] = result['prem2'] - medians['med_prem2'])
        # Wait, the presenter logic had a specific remapping:
        # result['prem7'] = result['prem2'] - medians['med_prem2'] -> This seems to imply prem7 output corresponds to prem2 input?
        # Let's look closely at presenter logic:
        # SQL logic: prem1..prem8 are rank-based. 
        # Presenter Logic around line 328:
        # result['prem1'] = result['prem1'] - medians['med_prem1']
        # result['prem7'] = result['prem2'] - medians['med_prem2']  <-- This looks like a specific business logic shift or a typo in the presenter script.
        # User said: "Dont change the logic"
        # I MUST follow the presenter logic exactly, even if it looks odd.
        # BUT, my get_annualized_forward_premiums returns labeled columns (prem1, prem7, prem30...) directly, 
        # whereas the SQL approach cited in the presenter's comments ('prem1-8') seems to be intermediate.
        # The presenter's `get_annualized_forward_premiums` returns columns: prem1, prem7, prem30, prem60, prem90, prem180, prem270, prem360.
        # Then `get_forward_premiums_vs_sample_median` calls that function.
        # AND THEN lines 297-306 in presenter: it joins `prem1`...`prem6`, `prem7`(anchor), `prem8`.
        # Wait, the presenter's `get_forward_premiums_vs_sample_median` function RE-IMPLEMENTS the ranking logic, it does NOT call `get_annualized_forward_premiums`.
        # It creates generic names `prem1` to `prem6` for below ranks, `prem7` for anchor, `prem8` for above.
        # Let's replicate `get_forward_premiums_vs_sample_median` fully independently to ensure exact logic match.
        
        df_dev = df.copy()
        df_dev["dist_270"] = (df_dev["days_to_expiry"] - 270).abs()
        df_dev["anchor_rank"] = df_dev.sort_values(["ran_at_utc", "dist_270", "days_to_expiry"]).groupby("ran_at_utc").cumcount() + 1
        
        anchors = df_dev[df_dev["anchor_rank"] == 1][["ran_at_utc", "days_to_expiry"]].rename(columns={"days_to_expiry": "anchor_days_to_expiry"})
        df_dev = df_dev.merge(anchors, on="ran_at_utc", how="left")
        
        below = df_dev[df_dev["days_to_expiry"] < df_dev["anchor_days_to_expiry"]].copy()
        above = df_dev[df_dev["days_to_expiry"] > df_dev["anchor_days_to_expiry"]].copy()
        
        below["below_rank"] = below.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, False]).groupby("ran_at_utc").cumcount() + 1
        above["above_rank"] = above.sort_values(["ran_at_utc", "days_to_expiry"], ascending=[True, True]).groupby("ran_at_utc").cumcount() + 1

        def pick(d, r_col, r, name): return d[d[r_col] == r].set_index("ran_at_utc")["annualized_pct"].rename(name)

        # Logic from presenter lines 287-306:
        # prem1..6 from below, prem7 is anchor, prem8 is above
        anchor_prem = df_dev[df_dev["anchor_rank"] == 1].set_index("ran_at_utc")["annualized_pct"].rename("prem7")
        
        res = anchors.set_index("ran_at_utc")[[]]
        res = res.join([
            pick(below, "below_rank", 6, "prem1"),
            pick(below, "below_rank", 5, "prem2"),
            pick(below, "below_rank", 4, "prem3"),
            pick(below, "below_rank", 3, "prem4"),
            pick(below, "below_rank", 2, "prem5"),
            pick(below, "below_rank", 1, "prem6"),
            anchor_prem,
            pick(above, "above_rank", 1, "prem8")
        ])
        
        res = res.reset_index()
        
        # Medians
        medians = {}
        for i in range(1, 9):
            col = f"prem{i}"
            if col in res.columns:
                medians[f"med_prem{i}"] = res[col].median()
            else:
                 medians[f"med_prem{i}"] = 0

        # Subtractions and Mapping (Presenter Lines 328-335)
        # Note: preserve original prem7 beforeoverwrite
        if "prem7" in res.columns: original_prem7 = res["prem7"].copy()
        
        # MAPPINGS:
        # prem1 (T_1)   = prem1 - med1
        # prem7 (T_7)   = prem2 - med2
        # prem30 (T_30) = prem3 - med3
        # ...
        
        out = pd.DataFrame()
        out["ran_at_utc"] = res["ran_at_utc"]
        
        if "prem1" in res.columns: out["prem1"]   = res["prem1"] - medians["med_prem1"]
        if "prem2" in res.columns: out["prem7"]   = res["prem2"] - medians["med_prem2"]
        if "prem3" in res.columns: out["prem30"]  = res["prem3"] - medians["med_prem3"]
        if "prem4" in res.columns: out["prem60"]  = res["prem4"] - medians["med_prem4"]
        if "prem5" in res.columns: out["prem90"]  = res["prem5"] - medians["med_prem5"]
        if "prem6" in res.columns: out["prem180"] = res["prem6"] - medians["med_prem6"]
        if "prem7" in res.columns: out["prem270"] = original_prem7 - medians["med_prem7"]
        if "prem8" in res.columns: out["prem360"] = res["prem8"] - medians["med_prem8"]
        
        # Rename to dev_X to distinguish from raw premiums
        rename_map = {
            "prem1": "dev_1",
            "prem7": "dev_7", # Logic mapped prem2->prem7, so output col name is prem7
            "prem30": "dev_30",
            "prem60": "dev_60",
            "prem90": "dev_90",
            "prem180": "dev_180",
            "prem270": "dev_270",
            "prem360": "dev_360"
        }
        out = out.rename(columns=rename_map)

        return out

    @staticmethod
    def get_forward_price_changes(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        # Logic: sort by time, unique time.
        # dASSET.F1 = LN(price[t+1]/price[t])
        # dASSET.F5 = LN(price[t+5]/price[t])
        
        df_s = df.sort_values("ran_at_utc").drop_duplicates(subset=["ran_at_utc"], keep="first").copy()
        
        price = df_s["spot_run"].astype(float)
        
        # Shift -1 means "next row" (future)
        df_s["f1"] = np.log(price.shift(-1) / price)
        df_s["f5"] = np.log(price.shift(-5) / price)
        
        return df_s[["ran_at_utc", "f1", "f5"]]

    @staticmethod
    def get_cross_correlations(df: pd.DataFrame, target_col: str, window: int = None, min_periods: int = 4) -> pd.DataFrame:
        # Generic correlation vs F1 or F5
        # Re-computes premiums internally as per presenter logic
        premiums = AnalysisService.get_annualized_forward_premiums(df)
        changes = AnalysisService.get_forward_price_changes(df)
        
        if premiums.empty or changes.empty: return pd.DataFrame()
        
        merged = premiums.merge(changes, on="ran_at_utc", how="inner").sort_values("ran_at_utc").reset_index(drop=True)
        
        result = merged[["ran_at_utc"]].copy()
        prem_cols = ["prem1", "prem7", "prem30", "prem60", "prem90", "prem180", "prem270", "prem360"]
        
        for col in prem_cols:
            if col not in merged.columns or target_col not in merged.columns:
                continue
            
            corrs = [None] * len(merged)
            for i in range(len(merged)):
                if i < min_periods - 1: continue
                
                if window is None:
                    # Expanding
                    data = merged.iloc[:i+1][[col, target_col]].dropna()
                else:
                    # Rolling
                    start = max(0, i - window + 1)
                    data = merged.iloc[start:i+1][[col, target_col]].dropna()
                
                if len(data) >= min_periods:
                    c = data[col].corr(data[target_col])
                    corrs[i] = None if pd.isna(c) else c
            
            result[col] = corrs
            
        return result

    @staticmethod
    def get_master_analysis(symbol: str):
        df = AnalysisService.get_raw_data(symbol)
        if df.empty:
            return None

        # 1. Spot
        spot = df.sort_values("ran_at_utc").drop_duplicates("ran_at_utc")[["ran_at_utc", "spot_run"]].rename(columns={"spot_run": "spot"})
        
        # 2. Days
        days = AnalysisService.get_days_to_expiry(df)
        
        # 3. Premiums
        prems = AnalysisService.get_annualized_forward_premiums(df)
        
        # 4. Deviations
        devs = AnalysisService.get_forward_premiums_vs_sample_median(df)
        
        # 5. Changes
        chgs = AnalysisService.get_forward_price_changes(df)
        
        # 6. Correlations F1
        corr_f1 = AnalysisService.get_cross_correlations(df, "f1")
        
        # 7. Correlations F5
        corr_f5 = AnalysisService.get_cross_correlations(df, "f5", min_periods=3)

        # Reformat for JSON (orient='records')
        def to_dict(d): return d.replace({np.nan: None}).to_dict(orient="records") if not d.empty else []

        return {
            "spot": to_dict(spot),
            "days_to_expiry": to_dict(days),
            "annualized_premiums": to_dict(prems),
            "premiums_vs_median": to_dict(devs),
            "price_changes": to_dict(chgs),
            "correlations_f1": to_dict(corr_f1),
            "correlations_f5": to_dict(corr_f5)
        }
