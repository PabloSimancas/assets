"use client";

import { useAssetDetail } from "../hooks/useAssetDetail";
import { Activity } from "lucide-react";
import { useState } from "react";
import MasterAnalysis from "./MasterAnalysis";

interface AssetDashboardProps {
    symbol: string;
}

export default function AssetDashboard({ symbol }: AssetDashboardProps) {
    const { data: asset, isLoading, error } = useAssetDetail(symbol);
    const [pages, setPages] = useState<{ id: string; name: string; widgets: any[] }[]>([
        { id: "1", name: "Master Analysis", widgets: [] }
    ]);
    const [activePageId, setActivePageId] = useState("1");
    const activePage = pages.find(p => p.id === activePageId);

    const handleAddPage = () => {
        const newId = (pages.length + 1).toString();
        const newPage = { id: newId, name: `Analysis ${newId}`, widgets: [] };
        setPages([...pages, newPage]);
        setActivePageId(newId);
    };

    if (isLoading) return (
        <div className="p-12 flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
            <p className="text-cyan-500 font-bold animate-pulse">Fetching {symbol} data...</p>
        </div>
    );

    if (error) return (
        <div className="p-12 text-center">
            <div className="inline-flex p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-500 mb-4">
                Error loading data: {(error as any).message}
            </div>
        </div>
    );

    if (!asset) return <div className="p-12 text-center text-gray-500">No data found for {symbol}</div>;

    return (
        <div className="flex flex-col h-full animate-in fade-in slide-in-from-bottom-4 duration-700 relative">
            {/* Asset Header */}
            <div className="p-4 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/[0.06] bg-white/[0.01] relative">
                <span className="absolute top-0 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-012</span>

                {/* Identity */}
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center text-black font-black text-xl shadow-xl shadow-cyan-500/20">
                        {asset.symbol[0]}
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-2xl font-black text-white tracking-tight leading-none drop-shadow-sm">
                                {asset.name}
                            </h2>
                            <span className="px-2 py-0.5 rounded-lg bg-white/5 border border-white/10 text-xs font-bold text-gray-400">
                                {asset.symbol}
                            </span>
                        </div>
                        <p className="text-xs font-medium text-gray-500 mt-1.5 uppercase tracking-widest flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                            {asset.category} Asset
                        </p>
                    </div>
                </div>

                {/* Tabs & Add Page */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
                    {pages.map(page => (
                        <button
                            key={page.id}
                            onClick={() => setActivePageId(page.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activePageId === page.id
                                ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/20"
                                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
                                }`}
                        >
                            {page.name}
                        </button>
                    ))}
                    <button
                        onClick={handleAddPage}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-dashed border-white/20 hover:border-white/40 transition-all whitespace-nowrap flex items-center gap-1"
                    >
                        <span>+</span> Add Analysis
                    </button>
                </div>
            </div>

            {/* Canvas Area (UI-011) */}
            <div className="p-4 md:p-6 h-full relative">
                <span className="absolute top-0 right-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-011</span>

                {/* Dynamic Content */}
                {activePageId === "1" ? (
                    <MasterAnalysis symbol={symbol} />
                ) : activePage && activePage.widgets.length === 0 ? (
                    <div className="h-[400px] border-2 border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center text-gray-500 gap-4 hover:border-cyan-500/30 hover:bg-white/[0.01] transition-all group cursor-pointer">
                        <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                            <Activity size={32} className="text-gray-400 group-hover:text-cyan-400 transition-colors" />
                        </div>
                        <div className="text-center space-y-1">
                            <h3 className="text-lg font-bold text-white">Empty Canvas</h3>
                            <p className="text-sm">Start by adding your first analysis module</p>
                        </div>
                        <button className="px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2 mt-2">
                            <span>+</span> Add Analysis Module
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* Placeholder for future widgets */}
                        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06] min-h-[200px] flex items-center justify-center text-gray-500">
                            Widget Area
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
