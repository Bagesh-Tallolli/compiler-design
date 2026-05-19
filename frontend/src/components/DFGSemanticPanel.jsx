import React, { useEffect, useMemo, useState } from 'react'
import DFGGraphView from './DFGGraphView'

export default function DFGSemanticPanel({ dfgData, onDownloadDFG }) {
  const [selectedFunction, setSelectedFunction] = useState(dfgData?.[0]?.function_name || '')

  useEffect(() => {
    setSelectedFunction(dfgData?.[0]?.function_name || '')
  }, [dfgData])

  const current = useMemo(() => {
    return dfgData?.find(item => item.function_name === selectedFunction) || dfgData?.[0] || null
  }, [dfgData, selectedFunction])

  const currentOldGraph = current?.old_graph
  const currentNewGraph = current?.new_graph

  const options = dfgData || []

  const memory = current?.memory_changes || {}
  const similarity = current?.similarity || {}
  const dfgChanges = current?.dfg_changes || []
  const dependencyChanges = current?.dependency_changes || []

  return (
    <div className="bg-white rounded shadow p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">DFG Semantic Diff</h3>
          <p className="text-sm text-gray-600 mt-1">Inspect arithmetic, memory, and dependency-flow changes.</p>
        </div>
        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={selectedFunction}
            onChange={(e) => setSelectedFunction(e.target.value)}
            className="border rounded px-3 py-2 text-sm bg-white"
          >
            {options.map(item => (
              <option key={item.function_name} value={item.function_name}>{item.function_name}</option>
            ))}
          </select>
          <button
            onClick={onDownloadDFG}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
          >
            ⬇ Download DFG JSON
          </button>
        </div>
      </div>

      {current ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="bg-gray-50 rounded p-3 border">
              <div className="text-xs text-gray-500">Similarity</div>
              <div className="text-xl font-semibold text-gray-900">{similarity.score ?? 0}%</div>
            </div>
            <div className="bg-gray-50 rounded p-3 border">
              <div className="text-xs text-gray-500">Loads</div>
              <div className="text-xl font-semibold text-gray-900">{memory.new?.load_count ?? 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-3 border">
              <div className="text-xs text-gray-500">Stores</div>
              <div className="text-xl font-semibold text-gray-900">{memory.new?.store_count ?? 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-3 border">
              <div className="text-xs text-gray-500">Memory Impact</div>
              <div className="text-sm font-semibold text-gray-900 mt-1">{memory.semantic_label || 'Unknown'}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <DFGGraphView title="Old DFG" graph={currentOldGraph} otherGraph={currentNewGraph} side="old" />
            <DFGGraphView title="New DFG" graph={currentNewGraph} otherGraph={currentOldGraph} side="new" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4 bg-gray-50">
              <h4 className="font-semibold text-gray-900 mb-3">DFG Changes</h4>
              <div className="space-y-2">
                {dfgChanges.map((change, index) => (
                  <div key={index} className={`p-3 rounded border ${change.impact === 'high' ? 'bg-red-50 border-red-200' : change.impact === 'medium' ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                    <div className="text-xs font-bold uppercase text-gray-600">{change.type.replace(/_/g, ' ')}</div>
                    <div className="text-sm mt-1 text-gray-900">{change.description}</div>
                  </div>
                ))}
                {dfgChanges.length === 0 && <div className="text-sm text-gray-500">No DFG structural changes detected.</div>}
              </div>
            </div>

            <div className="border rounded-lg p-4 bg-gray-50">
              <h4 className="font-semibold text-gray-900 mb-3">Dependency & Memory Report</h4>
              <div className="space-y-3 text-sm text-gray-800">
                <div>
                  <div className="font-medium text-gray-600">Dependency Changes</div>
                  {dependencyChanges.length > 0 ? (
                    dependencyChanges.map((item, index) => (
                      <div key={index} className="mt-2 p-3 bg-white rounded border">
                        <div>{item.description}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          +{item.added_edges?.length || 0} edges, -{item.removed_edges?.length || 0} edges
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-500">No dependency chain changes recorded.</div>
                  )}
                </div>
                <div>
                  <div className="font-medium text-gray-600">Memory Changes</div>
                  <div className="mt-2 p-3 bg-white rounded border space-y-1">
                    <div>Loads: {memory.old?.load_count ?? 0} → {memory.new?.load_count ?? 0}</div>
                    <div>Stores: {memory.old?.store_count ?? 0} → {memory.new?.store_count ?? 0}</div>
                    <div>Memory instructions: {memory.old?.memory_instruction_count ?? 0} → {memory.new?.memory_instruction_count ?? 0}</div>
                    <div>Pointer usage: {memory.old?.pointer_usage_count ?? 0} → {memory.new?.pointer_usage_count ?? 0}</div>
                    <div className="font-medium">Impact: {memory.impact || 'unknown'}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">No DFG analysis available.</div>
      )}
    </div>
  )
}
