
import React, { useEffect, useState } from 'react';
import apiClient from '@/lib/apiClient';
import AnalysisTable from './AnalysisTable';
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
            {/* Spot Prices */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-96 relative group">
                    <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">UI-013</span>
                    <AnalysisTable
                        title="Spot Prices"
                        data={data?.spot}
                        loading={loading}
                        columns={[dateCol, { key: 'spot', label: 'Spot Price', format: plainNum }]}
                    />
                </div>
                <div className="h-96 relative group">
                    <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">UI-014</span>
                    <AnalysisTable
                        title="Price Changes (Log Returns)"
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

            {/* Days Buckets */}
            <div className="h-96">
                <AnalysisTable
                    title="Days to Expiry Buckets"
                    data={data?.days_to_expiry}
                    loading={loading}
                    columns={[dateCol, ...daysCols]}
                />
            </div>

            {/* Annualized Premiums */}
            <div className="h-96">
                <AnalysisTable
                    title="Annualized Forward Premiums (%)"
                    data={data?.annualized_premiums}
                    loading={loading}
                    columns={[dateCol, ...premCols]}
                />
            </div>

            {/* Premiums vs Median */}
            <div className="h-96">
                <AnalysisTable
                    title="Premiums vs Sample Median"
                    data={data?.premiums_vs_median}
                    loading={loading}
                    columns={[dateCol, ...devCols]}
                />
            </div>

            {/* Correlations F1 */}
            <div className="h-96">
                <AnalysisTable
                    title="Cross Correlations vs F1"
                    data={data?.correlations_f1}
                    loading={loading}
                    columns={[dateCol, ...corrF1Cols]}
                />
            </div>

            {/* Correlations F5 */}
            <div className="h-96">
                <AnalysisTable
                    title="Cross Correlations vs F5"
                    data={data?.correlations_f5}
                    loading={loading}
                    columns={[dateCol, ...corrF5Cols]}
                />
            </div>
        </div>
    );
}
