
import React from 'react';

interface AnalysisTableProps {
    title: React.ReactNode;
    data: any[];
    columns: { key: string; label: string; format?: (val: any) => React.ReactNode }[];
    loading?: boolean;
}

export default function AnalysisTable({ title, data, columns, loading }: AnalysisTableProps) {
    if (loading) {
        return (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 h-full flex flex-col items-center justify-center gap-3 animate-pulse">
                <div className="h-4 w-32 bg-white/10 rounded" />
                <div className="h-4 w-64 bg-white/5 rounded" />
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 h-full flex items-center justify-center text-gray-500 text-xs">
                No data available
            </div>
        );
    }

    return (
        <div className="bg-[#151921]/50 backdrop-blur-sm border border-white/[0.06] rounded-2xl overflow-hidden flex flex-col h-full shadow-lg">
            <div className="px-4 py-3 border-b border-white/[0.06] bg-white/[0.02] flex items-center justify-between">
                <div>{typeof title === 'string' ? <h3 className="font-bold text-gray-200 text-xs uppercase tracking-wider">{title}</h3> : title}</div>
                <span className="text-[10px] text-gray-500 font-mono bg-white/5 px-2 py-0.5 rounded-full">{data.length} rows</span>
            </div>

            <div className="overflow-auto custom-scrollbar flex-1 relative">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1A1F2B] sticky top-0 z-10 shadow-sm">
                        <tr>
                            {columns.map((col) => (
                                <th key={col.key} className="px-3 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-white/[0.06] whitespace-nowrap">
                                    {col.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.03]">
                        {data.map((row, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors group">
                                {columns.map((col) => (
                                    <td key={col.key} className="px-3 py-2 text-[11px] text-gray-300 font-mono whitespace-nowrap group-hover:text-white transition-colors tabular-nums">
                                        {col.format ? col.format(row[col.key]) : row[col.key] ?? "-"}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
