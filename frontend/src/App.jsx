import React, { useState } from 'react';
import TestCodeEditor from './components/TestCodeEditor.jsx';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, GitGraph, FileCode2, Globe, FileOutput, UploadCloud, Rocket, FileText, Beaker } from 'lucide-react';
import PremiumDashboard from './components/PremiumDashboard';
import AnimatedPipeline from './components/AnimatedPipeline';
import RealWorldImpact from './components/RealWorldImpact';
import GraphVisualizer from './components/GraphVisualizer';
import EditorPane from './components/EditorPane';
import DiagnosticsView from './components/DiagnosticsView';
import { cn } from './utils';

// Hardcoded hackathon demos for instant wow-factor
const DEMOS = {
  DCE: {
    old: `int process(int x) {\n  int y = x * 2;\n  int z = y + 10;\n  int unused = z * 5;\n  return z;\n}`,
    new: `int process(int x) {\n  int y = x * 2;\n  int z = y + 10;\n  return z;\n}`
  },
  UNROLL: {
    old: `int unroll_test(int x) {\n  int sum = 0;\n  for(int i=0; i<4; i++) {\n    sum += x;\n  }\n  return sum;\n}`,
    new: `int unroll_test(int x) {\n  int sum = 0;\n  sum += x;\n  sum += x;\n  sum += x;\n  sum += x;\n  return sum;\n}`
  }
};

export default function App() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [alert, setAlert] = useState(null);
  const [graphMode, setGraphMode] = useState('cfg');

  const handleGenerate = async (file1, file2) => {
    const fOld = file1 || oldFile;
    const fNew = file2 || newFile;

    if (!fOld || !fNew) {
      setAlert({ type: 'error', msg: 'Please select both old and new source files.' });
      return;
    }

    const form = new FormData();
    form.append('old_file', fOld);
    form.append('new_file', fNew);

    try {
      setLoading(true);
      setPipelineRunning(true);
      setActiveTab('pipeline');
      setAlert(null);
      setData(null);

      const resp = await axios.post('http://localhost:8000/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      if (resp.data && resp.data.success) {
        setData(resp.data);
      } else {
        setAlert({ type: 'error', msg: resp.data.error || 'Unexpected response' });
        setPipelineRunning(false);
      }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e.message;
      setAlert({ type: 'error', msg });
      setPipelineRunning(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLoad = (demoKey) => {
    const oldBlob = new Blob([DEMOS[demoKey].old], { type: 'text/plain' });
    const newBlob = new Blob([DEMOS[demoKey].new], { type: 'text/plain' });
    const fOld = new File([oldBlob], `${demoKey.toLowerCase()}_old.cpp`);
    const fNew = new File([newBlob], `${demoKey.toLowerCase()}_new.cpp`);
    setOldFile(fOld);
    setNewFile(fNew);
    handleGenerate(fOld, fNew);
  };

  const NavButton = ({ id, label, icon: Icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={cn(
        "flex items-center space-x-3 w-full p-3 rounded-xl transition-all duration-200",
        activeTab === id 
          ? "bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.5)] text-white" 
          : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
      )}
    >
      <Icon className="w-5 h-5" />
      <span className="font-semibold">{label}</span>
    </button>
  );

  return (
    <div className="flex h-screen bg-[#0B1120] text-slate-200 overflow-hidden font-sans">
      
      {/* Sidebar Navigation */}
      <aside className="w-72 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800 p-6 flex flex-col h-full z-20">
        <div className="flex items-center space-x-3 mb-10">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-emerald-400 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <Beaker className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">Semantic Diff</h1>
            <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Research Engine</p>
          </div>
        </div>

        <nav className="space-y-2 flex-1">
          <NavButton id="dashboard" label="Intelligence Dashboard" icon={LayoutDashboard} />
          <NavButton id="impact" label="Real-World Impact" icon={Globe} />
          <NavButton id="graph" label="Graph Visualizer" icon={GitGraph} />
          <NavButton id="test" label="Manual Test" icon={FileCode2} />
          <NavButton id="ir" label="LLVM IR Source" icon={FileCode2} />
          <NavButton id="report" label="Semantic Report" icon={FileText} />
          <NavButton id="diagnostics" label="System Diagnostics" icon={LayoutDashboard} />
        </nav>

        {/* Upload & Hackathon Controls */}
        <div className="mt-8 space-y-4">
          <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <h3 className="text-xs uppercase tracking-widest text-slate-400 font-bold mb-3">Live Analysis</h3>
            <input type="file" onChange={e => setOldFile(e.target.files[0])} className="text-xs mb-2 block w-full text-slate-400 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer" />
            <input type="file" onChange={e => setNewFile(e.target.files[0])} className="text-xs mb-4 block w-full text-slate-400 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer" />
            <button onClick={() => handleGenerate()} disabled={loading} className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-lg text-sm font-bold shadow-lg disabled:opacity-50 transition-all">
              {loading ? 'Initializing...' : 'Run Analysis'}
            </button>
          </div>

          <div className="p-4 bg-purple-900/20 rounded-xl border border-purple-500/30">
            <h3 className="text-xs uppercase tracking-widest text-purple-400 font-bold mb-3 flex items-center"><Rocket className="w-3 h-3 mr-2"/> Hackathon Demos</h3>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => handleDemoLoad('DCE')} className="py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded text-slate-300">Run DCE</button>
              <button onClick={() => handleDemoLoad('UNROLL')} className="py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded text-slate-300">Run Unroll</button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative overflow-y-auto overflow-x-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-[#0B1120] to-[#0B1120]">
        
        {alert && (
          <div className="absolute top-4 right-4 z-50 p-4 rounded-xl border shadow-2xl backdrop-blur-md max-w-sm" style={{ borderColor: alert.type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)', backgroundColor: alert.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)' }}>
            <p className={alert.type === 'error' ? 'text-red-400 font-medium text-sm' : 'text-emerald-400 font-medium text-sm'}>{alert.msg}</p>
          </div>
        )}

        <AnimatePresence mode="wait">
          
          {/* PIPELINE VIEW */}
          {activeTab === 'pipeline' && (
            <motion.div key="pipeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="min-h-full flex items-center justify-center">
              <AnimatedPipeline isRunning={pipelineRunning} onComplete={() => { setPipelineRunning(false); setActiveTab('dashboard'); }} />
            </motion.div>
          )}

          {/* DASHBOARD VIEW */}
          {activeTab === 'dashboard' && data && !pipelineRunning && (
            <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <PremiumDashboard data={data} />
            </motion.div>
          )}

          {/* IMPACT VIEW */}
          {activeTab === 'impact' && data && !pipelineRunning && (
            <motion.div key="impact" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <RealWorldImpact classifications={data.classifications} />
            </motion.div>
          )}

          {/* GRAPH VIEW */}
          {activeTab === 'graph' && data && !pipelineRunning && (
            <motion.div key="graph" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-8 max-w-7xl mx-auto h-full flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">Graph Visualizer</h2>
                  <p className="text-slate-400">Interactive Control Flow and Data Flow extraction.</p>
                </div>
                <div className="flex bg-slate-800 p-1 rounded-lg">
                  <button onClick={() => setGraphMode('cfg')} className={cn("px-4 py-2 rounded-md text-sm font-semibold transition-all", graphMode === 'cfg' ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-white")}>CFG</button>
                  <button onClick={() => setGraphMode('dfg')} className={cn("px-4 py-2 rounded-md text-sm font-semibold transition-all", graphMode === 'dfg' ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-white")}>DFG</button>
                </div>
              </div>
              <GraphVisualizer cfgData={data.cfg_analysis} dfgData={data.dfg_analysis} mode={graphMode} />
            </motion.div>
          )}
          {activeTab === 'test' && (
            <motion.div key="test" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-4">
              <TestCodeEditor />
            </motion.div>
          )}

          {/* IR VIEW */}
          {activeTab === 'ir' && data && !pipelineRunning && (
            <motion.div key="ir" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-8 h-full flex flex-col">
              <h2 className="text-3xl font-bold text-white mb-6">LLVM Intermediate Representation</h2>
              <div className="flex-1 grid grid-cols-2 gap-6 min-h-[600px]">
                <EditorPane title="Old IR (Normalized)" value={data.normalized_old_ir} language="llvm" />
                <EditorPane title="New IR (Normalized)" value={data.normalized_new_ir} language="llvm" />
              </div>
            </motion.div>
          )}

          {/* REPORT VIEW */}
          {activeTab === 'report' && data && !pipelineRunning && (
            <motion.div key="report" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-8 max-w-5xl mx-auto h-full flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">Semantic Evaluation Report</h2>
                  <p className="text-slate-400">Full textual breakdown generated by the Semantic AI.</p>
                </div>
                <button onClick={() => {
                  const a = document.createElement('a');
                  const blob = new Blob([data.report_text], {type: 'text/plain'});
                  a.href = URL.createObjectURL(blob);
                  a.download = 'semantic_report.txt';
                  a.click();
                }} className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-bold text-white shadow-lg transition-all">
                  <FileOutput className="w-4 h-4 mr-2" /> Export TXT
                </button>
              </div>
              <div className="flex-1 bg-slate-900/80 border border-slate-700/50 rounded-2xl p-6 overflow-y-auto font-mono text-sm text-slate-300 shadow-2xl backdrop-blur-xl whitespace-pre-wrap">
                {data.report_text}
              </div>
            </motion.div>
          )}

          {/* DIAGNOSTICS VIEW */}
          {activeTab === 'diagnostics' && !pipelineRunning && (
            <motion.div key="diagnostics" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
              <DiagnosticsView />
            </motion.div>
          )}

          {/* EMPTY STATE */}
          {!data && !pipelineRunning && activeTab !== 'diagnostics' && activeTab !== 'test' && (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col items-center justify-center text-slate-500">
              <UploadCloud className="w-24 h-24 mb-6 opacity-20" />
              <h2 className="text-2xl font-bold text-slate-400 mb-2">Awaiting Analysis Data</h2>
              <p className="max-w-md text-center text-slate-500">Upload C++ source files or run a Hackathon Demo from the sidebar to visualize the compiler changes.</p>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
}
