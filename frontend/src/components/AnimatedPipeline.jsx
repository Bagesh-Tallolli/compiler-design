import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { cn } from '../utils';

const STAGES = [
  { id: 'upload', label: 'Source Code Uploaded', desc: 'C/C++ files received' },
  { id: 'ir', label: 'LLVM IR Generation', desc: 'Compiling down to intermediate representation' },
  { id: 'norm', label: 'IR Normalization', desc: 'Stripping volatile metadata & canonicalizing' },
  { id: 'cfg', label: 'CFG Extraction', desc: 'Building Control Flow Graph' },
  { id: 'dfg', label: 'DFG Extraction', desc: 'Building Data Flow Graph' },
  { id: 'opt', label: 'Optimization Detection', desc: 'Detecting DCE, Unrolling, etc.' },
  { id: 'semantic', label: 'Semantic AI Classification', desc: 'Assigning risk & impact' }
];

export default function AnimatedPipeline({ isRunning, onComplete }) {
  const [activeStage, setActiveStage] = useState(-1);

  useEffect(() => {
    if (isRunning) {
      setActiveStage(0);
      let current = 0;
      const interval = setInterval(() => {
        current += 1;
        setActiveStage(current);
        if (current >= STAGES.length) {
          clearInterval(interval);
          if (onComplete) onComplete();
        }
      }, 600); // Hackathon-friendly fast stagger
      return () => clearInterval(interval);
    } else {
      setActiveStage(-1);
    }
  }, [isRunning, onComplete]);

  return (
    <div className="w-full max-w-4xl mx-auto p-8">
      <h2 className="text-2xl font-bold text-white mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
        Live Analysis Pipeline
      </h2>
      <div className="relative">
        {/* Connecting Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-800" />
        <motion.div 
          className="absolute left-8 top-0 w-0.5 bg-blue-500 shadow-[0_0_10px_#3b82f6]"
          initial={{ height: '0%' }}
          animate={{ height: activeStage >= 0 ? `${(Math.min(activeStage, STAGES.length - 1) / (STAGES.length - 1)) * 100}%` : '0%' }}
          transition={{ duration: 0.5 }}
        />

        <div className="space-y-8 relative z-10">
          {STAGES.map((stage, idx) => {
            const isCompleted = activeStage > idx;
            const isCurrent = activeStage === idx;
            const isPending = activeStage < idx;

            return (
              <motion.div 
                key={stage.id}
                className={cn(
                  "flex items-center space-x-6 p-4 rounded-xl backdrop-blur-md border transition-all duration-300",
                  isCompleted ? "bg-emerald-500/10 border-emerald-500/30" : 
                  isCurrent ? "bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]" : 
                  "bg-slate-900/50 border-slate-800 opacity-50"
                )}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: isPending && activeStage === -1 ? 0 : 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <div className="relative flex-shrink-0 flex items-center justify-center w-8 h-8">
                  {isCompleted ? (
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                  ) : isCurrent ? (
                    <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                  ) : (
                    <Circle className="w-8 h-8 text-slate-600" />
                  )}
                </div>
                <div>
                  <h3 className={cn("text-lg font-semibold", isCompleted ? "text-emerald-300" : isCurrent ? "text-blue-300" : "text-slate-400")}>
                    {stage.label}
                  </h3>
                  <p className="text-slate-500 text-sm">{stage.desc}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  );
}
