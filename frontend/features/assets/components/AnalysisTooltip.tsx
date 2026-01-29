import React from 'react';
import { HelpCircle } from 'lucide-react';

interface AnalysisTooltipProps {
    title: string;
    definition: string;
    interpretation: {
        label: string;
        value: string;
        color?: string; // e.g. "text-emerald-400"
    }[];
}

export default function AnalysisTooltip({ title, definition, interpretation }: AnalysisTooltipProps) {
    return (
        <div className="relative group inline-flex items-center gap-2 cursor-help z-50">
            <h3 className="font-bold text-gray-200 text-sm uppercase tracking-wider">{title}</h3>
            <HelpCircle size={14} className="text-gray-500 group-hover:text-cyan-400 transition-colors" />

            {/* Tooltip Card */}
            <div className="absolute left-0 top-full pt-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 transform translate-y-2 group-hover:translate-y-0 w-80 z-[100]">
                <div className="bg-[#0f1219] border border-white/10 rounded-xl p-4 shadow-2xl shadow-black/50 backdrop-blur-xl">
                    {/* Header */}
                    <div className="mb-3 pb-3 border-b border-white/5">
                        <h4 className="text-sm font-bold text-white mb-1">{title}</h4>
                        <p className="text-xs text-gray-400 leading-relaxed font-sans">{definition}</p>
                    </div>

                    {/* Interpretation */}
                    <div>
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-2">How to read it</p>
                        <div className="space-y-2">
                            {interpretation.map((item, idx) => (
                                <div key={idx} className="flex gap-2 items-start">
                                    <div className={`w-1 h-1 mt-1.5 rounded-full ${item.color || 'bg-gray-500'}`} />
                                    <div>
                                        <p className={`text-xs font-bold ${item.color || 'text-gray-200'}`}>{item.label}</p>
                                        <p className="text-[10px] text-gray-400 leading-tight">{item.value}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
