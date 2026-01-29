
import React, { useEffect, useState } from 'react';
import apiClient from '@/lib/apiClient';
import AnalysisTable from './AnalysisTable';
import AnalysisTooltip from './AnalysisTooltip';
import { format } from 'date-fns';

interface MasterAnalysisProps {
    symbol: string;
}

export default function MasterAnalysis({ symbol }: MasterAnalysisProps) {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let intervalId: NodeJS.Timeout;

        const fetchAnalysis = async () => {
            // Only show loading spinner on first load, not polling
            if (!data) setLoading(true);
            try {
                const response = await apiClient.get(`/analysis/${symbol}/master`);
                setData(response.data);
                setError(null);
            } catch (err) {
                console.error(err);
                if (!data) setError("Failed to load analysis data");
            } finally {
                setLoading(false);
            }
        };

        if (symbol) {
            fetchAnalysis();
            // Poll every 24 hours
            intervalId = setInterval(fetchAnalysis, 86400000);
        }

        return () => {
            if (intervalId) clearInterval(intervalId);
        };
    }, [symbol]);

    if (error) {
        return (
            <div className="p-8 text-center text-rose-500 bg-rose-500/10 rounded-2xl border border-rose-500/20">
                {error}
            </div>
        );
    }

    // UTILS
    const formatDate = (val: string) => val ? format(new Date(val), 'dd MMM yyyy') : '-';
    const numFormat = (val: any) => {
        if (typeof val !== 'number') return '-';
        return <span className={val < 0 ? 'text-rose-400' : 'text-emerald-400'}>{val.toFixed(2)}</span>;
    };
    const plainNum = (val: any) => typeof val === 'number' ? val.toFixed(2) : '-';

    // COLUMN DEFINITIONS
    const dateCol = { key: 'ran_at_utc', label: 'Date', format: formatDate };
    const daysCols = [
        { key: 't_270', label: 'T270 (Anchor)' },
        { key: 't_1', label: 'T1' },
        { key: 't_7', label: 'T7' },
        { key: 't_30', label: 'T30' },
        { key: 't_60', label: 'T60' },
        { key: 't_90', label: 'T90' },
        { key: 't_180', label: 'T180' },
        { key: 't_360', label: 'T360' },
    ];

    // Premiums & Devs columns
    const premCols = ['prem1', 'prem7', 'prem30', 'prem60', 'prem90', 'prem180', 'prem270', 'prem360'].map(k => ({
        key: k, label: k.toUpperCase(), format: numFormat
    }));

    const devCols = ['dev_1', 'dev_7', 'dev_30', 'dev_60', 'dev_90', 'dev_180', 'dev_270', 'dev_360'].map(k => ({
        key: k, label: k.toUpperCase(), format: numFormat
    }));

    const corrF1Cols = ['prem1', 'prem7', 'prem30', 'prem60', 'prem90', 'prem180', 'prem270', 'prem360'].map(k => ({
        key: k, label: k.toUpperCase(), format: numFormat
    }));
    const corrF5Cols = ['prem1', 'prem7', 'prem30', 'prem60', 'prem90', 'prem180', 'prem270', 'prem360'].map(k => ({
        key: k, label: k.toUpperCase(), format: numFormat
    }));


    return (
        <div className="space-y-6 pb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Row 1: Core Data (Spot, Expiry, Returns) */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                {/* Spot Prices */}
                <div className="h-72 relative group">
                    <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">UI-013</span>
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Spot Prices"
                                definition="The current market price of the asset for immediate delivery (e.g. BTC/USD)."
                                interpretation={[
                                    { label: "Trend", value: "Visualizes the underlying asset's price movement over time.", color: "text-gray-200" }
                                ]}
                            />
                        }
                        data={data?.spot}
                        loading={loading}
                        columns={[dateCol, { key: 'spot', label: 'Spot Price', format: plainNum }]}
                    />
                </div>

                {/* Days to Expiry Buckets */}
                <div className="h-72">
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Days to Expiry Buckets"
                                definition="Categorizes forward contracts into standardized time horizons to analyze term structure."
                                interpretation={[
                                    { label: "Columns", value: "Represents contracts expiring in roughly X days.", color: "text-gray-400" },
                                    { label: "Purpose", value: "Allows comparing contracts with similar maturities over time.", color: "text-gray-200" }
                                ]}
                            />
                        }
                        data={data?.days_to_expiry}
                        loading={loading}
                        columns={[dateCol, ...daysCols]}
                    />
                </div>

                {/* Price Changes */}
                <div className="h-72 relative group">
                    <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">UI-014</span>
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Price Changes (Log Returns)"
                                definition="Tracks the daily (f1) and 5-day (f5) percentage change in the price of the forward contracts."
                                interpretation={[
                                    { label: "High Volatility", value: "Large spikes indicate the market is pricing in new information aggressively.", color: "text-amber-400" },
                                    { label: "Divergence", value: "If Spot is flat but Forwards are moving, the expectation of the future is changing.", color: "text-cyan-400" }
                                ]}
                            />
                        }
                        data={data?.price_changes}
                        loading={loading}
                        columns={[
                            dateCol,
                            { key: 'f1', label: 'F1 (Next Day)', format: numFormat },
                            { key: 'f5', label: 'F5 (5 Days)', format: numFormat }
                        ]}
                    />
                </div>
            </div>

            {/* Row 2: Premiums */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Annualized Premiums */}
                <div className="h-72">
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Annualized Forward Premiums (%)"
                                definition="This chart displays the annualized cost (or yield) of holding a futures contract compared to the spot price across different expiry dates."
                                interpretation={[
                                    { label: "Green (Positive)", value: "Contango. The market expects prices to rise or there is a cost to carry.", color: "text-emerald-400" },
                                    { label: "Red (Negative)", value: "Backwardation. The market expects prices to fall (or high demand for immediate assets).", color: "text-rose-400" }
                                ]}
                            />
                        }
                        data={data?.annualized_premiums}
                        loading={loading}
                        columns={[dateCol, ...premCols]}
                    />
                </div>

                {/* Premiums vs Median */}
                <div className="h-72">
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Premiums vs Sample Median"
                                definition="Shows how the current premium deviates from its historical median (typical) value."
                                interpretation={[
                                    { label: "Near Zero", value: "The market is behaving normally.", color: "text-gray-400" },
                                    { label: "High Positive", value: "Asset is expensive relative to history (Overbought).", color: "text-emerald-400" },
                                    { label: "Low Negative", value: "Asset is cheap relative to history (Oversold).", color: "text-rose-400" }
                                ]}
                            />
                        }
                        data={data?.premiums_vs_median}
                        loading={loading}
                        columns={[dateCol, ...devCols]}
                    />
                </div>
            </div>

            {/* Row 3: Correlations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Correlations F1 */}
                <div className="h-72">
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Cross Correlations vs F1"
                                definition="Measures the correlation between changes in the Forward Premium and the underlying Spot Price (1-day changes)."
                                interpretation={[
                                    { label: "Positive (+1)", value: "Premium expands as Spot Price rises (Bullish Sentiment).", color: "text-emerald-400" },
                                    { label: "Negative (-1)", value: "Premium contracts as Spot Price rises (Bearish/Hedging).", color: "text-rose-400" }
                                ]}
                            />
                        }
                        data={data?.correlations_f1}
                        loading={loading}
                        columns={[dateCol, ...corrF1Cols]}
                    />
                </div>

                {/* Correlations F5 */}
                <div className="h-72">
                    <AnalysisTable
                        title={
                            <AnalysisTooltip
                                title="Cross Correlations vs F5"
                                definition="Measures the correlation between changes in the Forward Premium and the underlying Spot Price (5-day changes)."
                                interpretation={[
                                    { label: "Positive (+1)", value: "Premium expands as Spot Price rises (Bullish Sentiment).", color: "text-emerald-400" },
                                    { label: "Negative (-1)", value: "Premium contracts as Spot Price rises (Bearish/Hedging).", color: "text-rose-400" }
                                ]}
                            />
                        }
                        data={data?.correlations_f5}
                        loading={loading}
                        columns={[dateCol, ...corrF5Cols]}
                    />
                </div>
            </div>
        </div>
    );
}
