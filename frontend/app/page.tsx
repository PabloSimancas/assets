"use client";

import { useState } from "react";
import AssetDashboard from "@/features/assets/components/AssetDashboard";
import { useAssets } from "@/features/assets/hooks/useAssets";
import { Search, Bell, User, LayoutDashboard, BarChart2, Settings } from "lucide-react";

export default function Home() {
  const { data: assets, isLoading, isError, error } = useAssets();
  const [selectedSymbol, setSelectedSymbol] = useState("BTC");

  return (
    <main className="min-h-screen bg-[#0C0E12] text-gray-300 selection:bg-cyan-500/20 relative">
      {/* Top Navigation */}
      <header className="border-b border-white/[0.06] p-4 sticky top-0 bg-[#0C0E12]/80 backdrop-blur-xl z-50 relative">
        <span className="absolute top-0 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-001</span>
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-10 relative">
            <span className="absolute -top-2 -left-2 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-002</span>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <span className="bg-gradient-to-br from-cyan-400 to-teal-500 w-8 h-8 rounded-lg flex items-center justify-center text-black shadow-lg shadow-cyan-500/20">
                <LayoutDashboard size={18} strokeWidth={2.5} />
              </span>
              ASSETS
            </h1>
            <nav className="hidden md:flex items-center gap-8 text-sm font-medium relative">
              <span className="absolute -top-3 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-003</span>
              <span className="text-cyan-400 flex items-center gap-2 cursor-pointer pt-1 relative after:content-[''] after:absolute after:bottom-[-21px] after:left-0 after:w-full after:h-[2px] after:bg-cyan-400">
                Dashboard
              </span>
              <span className="text-gray-500 hover:text-white transition-colors flex items-center gap-2 cursor-pointer hover:bg-white/5 px-2 py-1 rounded-md">
                Markets
              </span>
              <span className="text-gray-500 hover:text-white transition-colors flex items-center gap-2 cursor-pointer hover:bg-white/5 px-2 py-1 rounded-md">
                Settings
              </span>
            </nav>
          </div>

          <div className="flex items-center gap-6">
            <div className="relative hidden lg:block group">
              <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-004</span>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-cyan-400 transition-colors" size={16} />
              <input
                type="text"
                placeholder="Search assets..."
                className="bg-white/[0.03] border border-white/[0.06] rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-cyan-500/30 focus:bg-white/[0.05] w-64 transition-all placeholder:text-gray-600"
              />
            </div>
            <div className="flex items-center gap-4 text-gray-400 relative">
              <span className="absolute -top-3 right-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-005</span>
              <div className="p-2 hover:bg-white/5 rounded-full cursor-pointer transition-colors relative">
                <Bell size={20} />
                <span className="absolute top-2 right-2.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0C0E12]"></span>
              </div>
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-500 to-teal-400 p-[2px] ring-2 ring-white/5 cursor-pointer">
                <div className="w-full h-full rounded-full bg-[#151921] flex items-center justify-center text-white font-semibold text-xs">
                  JD
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-[1600px] mx-auto p-4 md:p-6 lg:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Watchlist */}
          <aside className="lg:col-span-3 space-y-4 relative">
            <span className="absolute -top-2 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-006</span>
            <div className="bg-[#151921]/50 backdrop-blur-md rounded-3xl border border-white/[0.06] overflow-hidden shadow-2xl shadow-black/20">
              <div className="p-4 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.01] relative">
                <span className="absolute top-0 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-007</span>
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-2">Watchlist</h3>
                <span className="text-[10px] bg-cyan-500/10 text-cyan-400 px-2.5 py-1 rounded-full font-bold uppercase tracking-wide border border-cyan-500/10">Live Market</span>
              </div>

              <div className="p-2 space-y-1 relative">
                <span className="absolute top-0 right-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-008</span>
                {isLoading ? (
                  [1, 2, 3, 4].map(i => <div key={i} className="h-16 bg-white/[0.02] rounded-2xl animate-pulse m-2" />)
                ) : isError ? (
                  <div className="p-4 m-2 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <div className="text-red-400 font-bold text-xs mb-1">Connection Error</div>
                    <div className="text-[10px] text-red-400/70">
                      {error instanceof Error ? error.message : "Failed to load assets"}
                    </div>
                    <div className="text-[9px] text-gray-500 mt-2 font-mono break-all">
                      Check console for details
                    </div>
                  </div>
                ) : (
                  (assets && assets.length > 0) ? (
                    assets.map((asset) => (
                      <div
                        key={asset.symbol}
                        onClick={() => setSelectedSymbol(asset.symbol)}
                        className={`relative flex items-center justify-between p-3 rounded-2xl cursor-pointer transition-all duration-300 group ${selectedSymbol === asset.symbol
                          ? 'bg-gradient-to-r from-cyan-500/10 to-transparent border border-cyan-500/20'
                          : 'hover:bg-white/[0.03] border border-transparent'
                          }`}
                      >
                        <span className="absolute top-0 right-0 bg-red-500/50 text-white text-[8px] px-0.5 z-[60] font-mono pointer-events-none hidden group-hover:block">UI-009</span>
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shadow-inner ${selectedSymbol === asset.symbol
                            ? 'bg-cyan-400 text-black shadow-cyan-500/20'
                            : 'bg-[#1E232E] text-gray-400'
                            }`}>
                            {asset.symbol[0]}
                          </div>
                          <div>
                            <div className={`font-bold transition-colors ${selectedSymbol === asset.symbol ? 'text-white' : 'text-gray-300 group-hover:text-white'}`}>
                              {asset.symbol}
                            </div>
                            <div className="text-[11px] text-gray-500 font-medium">{asset.name}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          {selectedSymbol === asset.symbol && (
                            <div className="text-[10px] text-cyan-400 font-bold animate-in fade-in slide-in-from-right-2">Active</div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-xs text-gray-500">
                      No assets found.
                    </div>
                  )
                )}
              </div>

              <div className="p-2 border-t border-white/[0.06] relative">
                <span className="absolute top-0 left-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-010</span>
                <button className="w-full py-3 rounded-xl text-xs font-bold text-gray-400 hover:text-white hover:bg-white/[0.05] transition-all flex items-center justify-center gap-2 group">
                  <span className="w-4 h-4 rounded-full border border-gray-600 flex items-center justify-center group-hover:border-white group-hover:bg-white group-hover:text-black transition-all">+</span>
                  Add Asset
                </button>
              </div>
            </div>
          </aside>

          {/* Main Content - Dashboard */}
          <section className="lg:col-span-9 space-y-6 relative">
            <span className="absolute -top-2 right-0 bg-red-500/50 text-white text-[10px] px-1 z-[60] font-mono pointer-events-none">UI-011</span>
            <div className="bg-[#151921]/30 backdrop-blur-sm p-1 rounded-3xl border border-white/[0.06] min-h-[600px] shadow-2xl">
              <AssetDashboard symbol={selectedSymbol} />
            </div>
          </section>
        </div>
      </div >
    </main >
  );
}
