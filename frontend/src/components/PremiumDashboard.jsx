import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, ShieldAlert, Cpu, Layers } from 'lucide-react';
import { cn } from '../utils';

export default function PremiumDashboard({ data }) {
  if (!data || !data.diff) return null;

  // Extract metrics from the backend data
  const summary = data.diff;
  const classifications = data.classifications || [];
  
  // Calculate Semantic Stability (0-100)
  // Base 100, minus 5 for each changed func, minus 15 for each high risk
  const highRiskCount = classifications.filter(c => c.risk_level === 'High').length;
  const changedCount = summary.changed_functions?.length || 0;
  const stability = Math.max(0, 100 - (changedCount * 5) - (highRiskCount * 15));

  // Determine overall risk
  let overallRisk = 'Low';
  let riskColor = 'text-emerald-400';
  let riskBg = 'bg-emerald-500/10 border-emerald-500/20';
  if (highRiskCount > 0) {
    overallRisk = 'High';
    riskColor = 'text-rose-400';
    riskBg = 'bg-rose-500/10 border-rose-500/20';
  } else if (classifications.some(c => c.risk_level === 'Medium')) {
    overallRisk = 'Medium';
    riskColor = 'text-amber-400';
    riskBg = 'bg-amber-500/10 border-amber-500/20';
  }

  // Gather unique optimizations
  const allGained = new Set();
  const allLost = new Set();
  classifications.forEach(c => {
    c.gained_optimizations.forEach(o => allGained.add(o));
    c.lost_optimizations.forEach(o => allLost.add(o));
  });

  // Calculate Delta Cyclomatic
  let totalCycloDelta = 0;
  if (data.cfg_analysis) {
    data.cfg_analysis.forEach(cfg => {
      totalCycloDelta += cfg.complexity?.delta?.cyclomatic_change || 0;
    });
  }

  const Card = ({ title, icon: Icon, children, className }) => (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("p-6 rounded-2xl backdrop-blur-xl border border-slate-700/50 bg-slate-900/60 shadow-xl", className)}
    >
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 bg-slate-800 rounded-lg">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200">{title}</h3>
      </div>
      {children}
    </motion.div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-blue-400 to-emerald-400">
          Semantic Intelligence Dashboard
        </h1>
        <p className="text-slate-400 mt-2">Deep graph-based analysis of compiler transformations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Risk Score Meter */}
        <Card title="Overall Risk Assessment" icon={ShieldAlert} className={riskBg}>
          <div className="flex flex-col items-center justify-center py-4">
            <span className={cn("text-5xl font-black tracking-wider drop-shadow-lg", riskColor)}>
              {overallRisk.toUpperCase()}
            </span>
            <span className="text-slate-400 mt-2 text-sm text-center">
              Based on structural CFG/DFG shifts
            </span>
          </div>
        </Card>

        {/* Semantic Stability */}
        <Card title="Semantic Stability" icon={Activity}>
          <div className="flex flex-col items-center justify-center py-4">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="64" cy="64" r="56" fill="none" stroke="#1e293b" strokeWidth="12" />
                <circle cx="64" cy="64" r="56" fill="none" stroke="url(#gradient)" strokeWidth="12" strokeDasharray="351.8" strokeDashoffset={351.8 - (351.8 * stability) / 100} className="transition-all duration-1000 ease-out" />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#10b981" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="absolute text-3xl font-bold text-white">{stability}%</span>
            </div>
          </div>
        </Card>

        {/* Complexity Delta */}
        <Card title="Structural Complexity" icon={Layers}>
          <div className="flex flex-col items-center justify-center py-4">
            <span className={cn("text-5xl font-black", totalCycloDelta > 0 ? "text-rose-400" : totalCycloDelta < 0 ? "text-emerald-400" : "text-slate-300")}>
              {totalCycloDelta > 0 ? '+' : ''}{totalCycloDelta}
            </span>
            <span className="text-slate-400 mt-2 text-sm text-center">
              Net Change in Cyclomatic Complexity
            </span>
          </div>
        </Card>

        {/* Optimization Summary */}
        <Card title="Compiler Optimizations" icon={Zap}>
          <div className="space-y-3 mt-2">
            {allGained.size === 0 && allLost.size === 0 && (
              <div className="text-slate-500 text-sm italic">No major optimizations detected.</div>
            )}
            {Array.from(allGained).map(opt => (
              <div key={opt} className="flex items-center space-x-2 text-sm bg-emerald-500/10 text-emerald-300 p-2 rounded">
                <span className="text-emerald-400 font-bold">✓</span>
                <span>{opt} Gained</span>
              </div>
            ))}
            {Array.from(allLost).map(opt => (
              <div key={opt} className="flex items-center space-x-2 text-sm bg-rose-500/10 text-rose-300 p-2 rounded">
                <span className="text-rose-400 font-bold">✗</span>
                <span>{opt} Lost</span>
              </div>
            ))}
          </div>
        </Card>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <Card title="Function Alterations" icon={Cpu} className="lg:col-span-2">
           <div className="grid grid-cols-3 gap-4 text-center">
             <div className="p-4 bg-slate-800/50 rounded-xl">
               <div className="text-3xl font-bold text-blue-400">{summary.changed_functions?.length || 0}</div>
               <div className="text-sm text-slate-400 mt-1">Modified</div>
             </div>
             <div className="p-4 bg-slate-800/50 rounded-xl">
               <div className="text-3xl font-bold text-emerald-400">{summary.unchanged_functions?.length || 0}</div>
               <div className="text-sm text-slate-400 mt-1">Identical</div>
             </div>
             <div className="p-4 bg-slate-800/50 rounded-xl">
               <div className="text-3xl font-bold text-rose-400">{(summary.added_functions?.length || 0) + (summary.removed_functions?.length || 0)}</div>
               <div className="text-sm text-slate-400 mt-1">Added / Removed</div>
             </div>
           </div>
        </Card>
      </div>

    </div>
  );
}
