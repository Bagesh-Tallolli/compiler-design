import React, { useMemo } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'

function colorForNode(node, otherTextSet, side) {
  const isShared = otherTextSet.has(node.text)
  if (side === 'old') {
    return isShared ? '#facc15' : '#ef4444'
  }
  return isShared ? '#facc15' : '#22c55e'
}

function buildElements(graph, otherGraph, side) {
  const otherTextSet = new Set((otherGraph?.nodes || []).map(node => node.text))
  const nodes = (graph?.nodes || []).map((node, index) => ({
    id: node.name,
    data: { label: node.text },
    position: { x: 40, y: index * 92 },
    style: {
      width: 280,
      padding: 10,
      borderRadius: 10,
      border: '1px solid #cbd5e1',
      background: colorForNode(node, otherTextSet, side),
      color: '#111827',
      fontSize: 11,
      lineHeight: 1.35,
      whiteSpace: 'pre-wrap',
    },
  }))

  const edges = (graph?.edges || []).map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    animated: edge.type !== 'data',
    style: { stroke: '#64748b', strokeWidth: 1.5 },
    labelStyle: { fill: '#334155', fontSize: 10 },
  }))

  return { nodes, edges }
}

export default function DFGGraphView({ title, graph, otherGraph, side }) {
  const elements = useMemo(() => buildElements(graph, otherGraph, side), [graph, otherGraph, side])

  return (
    <div className="h-[520px] border rounded-lg overflow-hidden bg-white">
      <div className="px-3 py-2 border-b bg-gray-50 text-sm font-semibold text-gray-800">{title}</div>
      <div className="h-[calc(100%-40px)]">
        <ReactFlow
          nodes={elements.nodes}
          edges={elements.edges}
          fitView
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
        >
          <MiniMap zoomable pannable />
          <Controls />
          <Background gap={16} size={1} color="#e2e8f0" />
        </ReactFlow>
      </div>
    </div>
  )
}
