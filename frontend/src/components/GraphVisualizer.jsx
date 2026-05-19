import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';

export default function GraphVisualizer({ cfgData, dfgData, mode = 'cfg' }) {
  // Convert custom CFG/DFG format to ReactFlow format
  const { nodes, edges } = useMemo(() => {
    let initialNodes = [];
    let initialEdges = [];

    if (!cfgData && !dfgData) return { nodes: [], edges: [] };

    if (mode === 'cfg' && cfgData && cfgData.length > 0) {
      // Just take the first function's old CFG for visualization to keep it simple
      // In a full implementation, you'd have a dropdown to select the function
      const firstFunc = cfgData[0];
      const cfgNodes = firstFunc.complexity?.old?.node_count || 5; 
      // Fallback dummy visualization if actual node structures aren't passed cleanly
      
      for (let i = 0; i < cfgNodes; i++) {
        initialNodes.push({
          id: `node_${i}`,
          data: { label: i === 0 ? 'Entry Block' : i === cfgNodes - 1 ? 'Exit Block' : `Basic Block ${i}` },
          position: { x: 250, y: i * 100 },
          style: {
            background: i === 0 ? '#10b981' : i === cfgNodes - 1 ? '#ef4444' : '#1e293b',
            color: '#fff',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '10px',
            width: 150,
          }
        });
        if (i < cfgNodes - 1) {
          initialEdges.push({
            id: `edge_${i}`,
            source: `node_${i}`,
            target: `node_${i+1}`,
            animated: true,
            style: { stroke: '#3b82f6', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' }
          });
        }
      }
    } else if (mode === 'dfg') {
      // DFG dummy generic viz
      initialNodes = [
        { id: '1', data: { label: 'Load %x' }, position: { x: 100, y: 50 }, style: { background: '#6366f1', color: 'white' } },
        { id: '2', data: { label: 'Load %y' }, position: { x: 300, y: 50 }, style: { background: '#6366f1', color: 'white' } },
        { id: '3', data: { label: 'Mul %tmp1' }, position: { x: 200, y: 150 }, style: { background: '#f59e0b', color: 'white' } },
        { id: '4', data: { label: 'Store %result' }, position: { x: 200, y: 250 }, style: { background: '#10b981', color: 'white' } },
      ];
      initialEdges = [
        { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#94a3b8' } },
        { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#94a3b8' } },
        { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#94a3b8' } },
      ];
    }

    return { nodes: initialNodes, edges: initialEdges };
  }, [cfgData, dfgData, mode]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-[600px] items-center justify-center bg-slate-900 border border-slate-800 rounded-xl">
        <p className="text-slate-500">Run an analysis to visualize the graph structure.</p>
      </div>
    );
  }

  return (
    <div className="h-[600px] w-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <ReactFlow 
        nodes={nodes} 
        edges={edges}
        fitView
        className="bg-slate-900"
      >
        <Background color="#334155" gap={16} />
        <Controls className="bg-slate-800 fill-white text-white border-none shadow-lg" />
      </ReactFlow>
    </div>
  );
}
