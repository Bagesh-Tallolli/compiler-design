import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Terminal, Cpu } from 'lucide-react';
import { cn } from '../utils';

export default function DiagnosticsView() {
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDiagnostics = async () => {
      try {
        const resp = await axios.get('http://localhost:8000/diagnostics');
        setDiagnostics(resp.data);
      } catch (err) {
        setError('Failed to load diagnostics. Backend may be offline.');
      } finally {
        setLoading(false);
      }
    };
    fetchDiagnostics();
  }, []);

  if (loading) return <div className="p-8 text-slate-400">Loading system diagnostics...</div>;
  if (error) return <div className="p-8 text-rose-400">{error}</div>;
  if (!diagnostics) return null;

  const StatusItem = ({ label, isSuccess, details }) => (
    <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 mb-3">
      <div className="flex items-center space-x-4">
        {isSuccess ? <CheckCircle className="w-6 h-6 text-emerald-400" /> : <XCircle className="w-6 h-6 text-rose-400" />}
        <div>
          <h4 className="font-semibold text-slate-200">{label}</h4>
          {details && <p className="text-xs text-slate-400 font-mono mt-1">{details}</p>}
        </div>
      </div>
      <div className={cn("px-3 py-1 rounded-full text-xs font-bold", isSuccess ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400")}>
        {isSuccess ? 'READY' : 'MISSING'}
      </div>
    </div>
  );

  return (
    <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">System Diagnostics</h2>
        <p className="text-slate-400">Verifying LLVM backend toolchain integration and health.</p>
      </div>

      <div className="space-y-6">
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
          <h3 className="text-xl font-bold flex items-center text-slate-200 mb-6"><Terminal className="w-5 h-5 mr-3 text-blue-400"/> LLVM Pipeline Status</h3>
          
          <StatusItem 
            label="Clang Compiler" 
            isSuccess={diagnostics.clang_detected} 
            details={diagnostics.clang_path || 'Not found in PATH'} 
          />
          <StatusItem 
            label="Clang Version" 
            isSuccess={diagnostics.clang_version && diagnostics.clang_version !== 'Unknown'} 
            details={diagnostics.clang_version} 
          />
          <StatusItem 
            label="LLVM Opt Tool" 
            isSuccess={diagnostics.opt_detected} 
            details="Used for -O0 to -O3 optimization passes"
          />
          <StatusItem 
            label="LLVM Disassembler" 
            isSuccess={diagnostics.llvm_dis_detected} 
            details="Required for bitcode processing"
          />
        </div>

        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
          <h3 className="text-xl font-bold flex items-center text-slate-200 mb-6"><Cpu className="w-5 h-5 mr-3 text-purple-400"/> API Backend Status</h3>
          <StatusItem label="FastAPI Server" isSuccess={true} details="http://localhost:8000" />
        </div>
      </div>
    </div>
  );
}
