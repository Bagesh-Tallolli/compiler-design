import React from 'react';
import { motion } from 'framer-motion';
import { Cloud, Gamepad2, BrainCircuit, ShieldAlert, Cpu, HeartPulse } from 'lucide-react';
import { cn } from '../utils';

export default function RealWorldImpact({ classifications }) {
  if (!classifications || classifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500">
        <HeartPulse className="w-16 h-16 mb-4 opacity-50" />
        <p className="text-lg">Upload files to run the Real-World Impact Engine.</p>
      </div>
    );
  }

  // Aggregate impacts based on classification and optimizations
  const impacts = [];

  classifications.forEach(func => {
    func.gained_optimizations.forEach(opt => {
      if (opt.includes("Dead Code")) {
        impacts.push({
          domain: 'Cloud Cost & Hosting',
          icon: Cloud,
          color: 'text-sky-400',
          bg: 'bg-sky-500/10 border-sky-500/30',
          title: 'Payload & Memory Reduced',
          desc: `Dead Code Elimination in @${func.name} shrinks binary size. Reduces cold-start latency in AWS Lambda and lowers ECR storage costs.`
        });
      }
      if (opt.includes("Unrolling")) {
        impacts.push({
          domain: 'Gaming & High-Frequency Trading',
          icon: Gamepad2,
          color: 'text-purple-400',
          bg: 'bg-purple-500/10 border-purple-500/30',
          title: 'Frame Rendering Speedup',
          desc: `Loop Unrolling in @${func.name} eliminates branch prediction overhead. Critical for rendering loops in game engines or matching engines in HFT.`
        });
      }
      if (opt.includes("Strength Reduction")) {
        impacts.push({
          domain: 'AI/ML & Edge Computing',
          icon: BrainCircuit,
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          title: 'Kernel Latency Decreased',
          desc: `Strength Reduction (e.g. shifts instead of multiplication) in @${func.name} preserves battery on edge IoT devices and speeds up math kernels.`
        });
      }
    });

    func.lost_optimizations.forEach(opt => {
      impacts.push({
        domain: 'Performance Regression',
        icon: Cpu,
        color: 'text-rose-400',
        bg: 'bg-rose-500/10 border-rose-500/30',
        title: `${opt} Lost`,
        desc: `The modification to @${func.name} broke the compiler's ability to perform ${opt}. Expect a CPU cycle increase.`
      });
    });

    if (func.risk_level === 'High') {
      impacts.push({
        domain: 'Cybersecurity & CI/CD',
        icon: ShieldAlert,
        color: 'text-orange-400',
        bg: 'bg-orange-500/10 border-orange-500/30',
        title: 'Semantic Breakage Risk',
        desc: `High structural alteration in @${func.name}. Could introduce timing attacks or logic bypasses. DO NOT merge without manual code review.`
      });
    }
  });

  // Default if no specific optimizations matched
  if (impacts.length === 0) {
    impacts.push({
      domain: 'General Software Health',
      icon: HeartPulse,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/30',
      title: 'Stable Refactoring',
      desc: 'The code changes maintain semantic equivalence. Safe to deploy across all environments with no unexpected side-effects.'
    });
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h2 className="text-3xl font-bold text-white mb-2">Real-World Impact Analysis</h2>
      <p className="text-slate-400 mb-8">Translating compiler-level structural shifts into tangible business consequences.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {impacts.map((impact, i) => {
          const Icon = impact.icon;
          return (
            <motion.div 
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={cn("p-6 rounded-2xl border backdrop-blur-md shadow-xl", impact.bg)}
            >
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-slate-900/50 rounded-xl">
                  <Icon className={cn("w-8 h-8", impact.color)} />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                    {impact.domain}
                  </div>
                  <h3 className={cn("text-xl font-bold mb-2", impact.color)}>
                    {impact.title}
                  </h3>
                  <p className="text-slate-300 leading-relaxed">
                    {impact.desc}
                  </p>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  );
}
