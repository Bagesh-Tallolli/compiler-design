import React, { useState } from 'react'

export default function CFGAnalysisPanel({ cfgData, onDownloadCFG }) {
  const [expandedFuncs, setExpandedFuncs] = useState({})

  const toggleExpanded = (funcName) => {
    setExpandedFuncs(prev => ({
      ...prev,
      [funcName]: !prev[funcName]
    }))
  }

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high_increase':
        return 'text-red-600'
      case 'moderate_increase':
        return 'text-yellow-600'
      case 'slight_increase':
        return 'text-blue-600'
      case 'decreased':
        return 'text-green-600'
      case 'unchanged':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const getChangeTypeColor = (type) => {
    switch (type) {
      case 'block_added':
      case 'branch_added':
      case 'loop_added':
        return 'bg-green-50 text-green-800 border-green-200'
      case 'block_removed':
      case 'branch_removed':
      case 'loop_removed':
        return 'bg-red-50 text-red-800 border-red-200'
      case 'block_split':
      case 'block_merge':
      case 'execution_path_changed':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-50 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="bg-white rounded shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">CFG Semantic Diff</h3>
        <button
          onClick={onDownloadCFG}
          className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
        >
          ⬇ Download CFG JSON
        </button>
      </div>

      <div className="space-y-4">
        {cfgData.map((funcAnalysis, idx) => {
          const expanded = expandedFuncs[funcAnalysis.function_name]
          const complexity = funcAnalysis.complexity || {}
          const complexityDelta = complexity.delta || {}
          const changeCount = funcAnalysis.change_count || 0

          return (
            <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleExpanded(funcAnalysis.function_name)}
                className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex justify-between items-center text-left"
              >
                <div className="flex-1">
                  <div className="font-mono font-semibold text-gray-900">{funcAnalysis.function_name}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {changeCount} CFG changes |
                    Complexity: {complexity.old?.cyclomatic || 0} → {complexity.new?.cyclomatic || 0}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {complexity.old && (
                    <div className="text-right text-sm">
                      <div className="text-gray-600">Cyclomatic</div>
                      <div className={`text-lg font-semibold ${getImpactColor(complexity.impact)}`}>
                        {complexity.old.cyclomatic} → {complexity.new.cyclomatic}
                      </div>
                    </div>
                  )}
                  <span className={expanded ? 'text-gray-600' : 'text-gray-400'}>▼</span>
                </div>
              </button>

              {expanded && (
                <div className="px-4 py-4 border-t border-gray-200 space-y-4">
                  {/* Complexity Summary */}
                  {complexity.old && (
                    <div className="bg-gray-50 p-3 rounded space-y-2">
                      <h4 className="font-medium text-gray-900 text-sm">Complexity Metrics</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="text-sm">
                          <div className="text-gray-600">Cyclomatic Complexity</div>
                          <div className="font-mono">{complexity.old.cyclomatic} → {complexity.new.cyclomatic}</div>
                        </div>
                        <div className="text-sm">
                          <div className="text-gray-600">Total Complexity</div>
                          <div className="font-mono">{complexity.old.total_complexity} → {complexity.new.total_complexity}</div>
                        </div>
                        <div className="text-sm">
                          <div className="text-gray-600">Loop Count</div>
                          <div className="font-mono">{complexity.old.loop_count} → {complexity.new.loop_count}</div>
                        </div>
                        <div className="text-sm">
                          <div className="text-gray-600">Impact</div>
                          <div className={`font-semibold capitalize ${getImpactColor(complexity.impact)}`}>
                            {complexity.impact.replace(/_/g, ' ')}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* CFG Changes */}
                  {changeCount > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm mb-2">CFG Changes</h4>
                      <div className="space-y-2">
                        {funcAnalysis.changes.map((change, cidx) => (
                          <div key={cidx} className={`p-3 rounded border ${getChangeTypeColor(change.type)}`}>
                            <div className="font-mono text-xs font-semibold uppercase">{change.type.replace(/_/g, ' ')}</div>
                            <div className="text-sm mt-1">{change.description}</div>
                            {change.impact && (
                              <div className="text-xs mt-1 opacity-75">Impact: {change.impact}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Graph Summary */}
                  {funcAnalysis.old_graph && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="bg-blue-50 p-3 rounded border border-blue-200">
                        <div className="text-sm font-medium text-blue-900">Old CFG</div>
                        <div className="text-xs text-blue-700 mt-1">
                          Nodes: {funcAnalysis.old_graph.node_count} | Edges: {funcAnalysis.old_graph.edge_count}
                        </div>
                      </div>
                      <div className="bg-green-50 p-3 rounded border border-green-200">
                        <div className="text-sm font-medium text-green-900">New CFG</div>
                        <div className="text-xs text-green-700 mt-1">
                          Nodes: {funcAnalysis.new_graph.node_count} | Edges: {funcAnalysis.new_graph.edge_count}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {cfgData.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No CFG analysis available. Upload and analyze files to see CFG comparisons.
        </div>
      )}
    </div>
  )
}
