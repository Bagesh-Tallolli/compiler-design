import React, { useState, useMemo } from 'react'

export default function FunctionDiffTable({ diffData, onSelectFunction, filterStatus, onFilterChange, onDownloadDiff }) {
  const allFunctions = useMemo(() => {
    const funcs = [
      ...diffData.changed.map(f => ({ ...f, status: 'changed' })),
      ...diffData.unchanged.map(f => ({ ...f, status: 'unchanged' })),
      ...diffData.added.map(f => ({ ...f, status: 'added' })),
      ...diffData.removed.map(f => ({ ...f, status: 'removed' })),
    ]
    return funcs
  }, [diffData])

  const filteredFunctions = useMemo(() => {
    if (filterStatus === 'all') return allFunctions
    return allFunctions.filter(f => f.status === filterStatus)
  }, [allFunctions, filterStatus])

  const getStatusColor = (status) => {
    switch (status) {
      case 'changed':
        return 'bg-yellow-50 text-yellow-800'
      case 'unchanged':
        return 'bg-green-50 text-green-800'
      case 'added':
        return 'bg-blue-50 text-blue-800'
      case 'removed':
        return 'bg-red-50 text-red-800'
      default:
        return 'bg-gray-50 text-gray-800'
    }
  }

  const getStatusBadge = (status) => {
    const colors = {
      changed: 'bg-yellow-100 text-yellow-800',
      unchanged: 'bg-green-100 text-green-800',
      added: 'bg-blue-100 text-blue-800',
      removed: 'bg-red-100 text-red-800',
    }
    return `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`
  }

  return (
    <div className="bg-white rounded shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Function Semantic Diff</h3>
        <button
          onClick={onDownloadDiff}
          className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
        >
          ⬇ Download JSON
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => onFilterChange('all')}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            filterStatus === 'all'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({allFunctions.length})
        </button>
        <button
          onClick={() => onFilterChange('changed')}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            filterStatus === 'changed'
              ? 'bg-yellow-600 text-white'
              : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
          }`}
        >
          Changed ({diffData.changed.length})
        </button>
        <button
          onClick={() => onFilterChange('unchanged')}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            filterStatus === 'unchanged'
              ? 'bg-green-600 text-white'
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          Unchanged ({diffData.unchanged.length})
        </button>
        <button
          onClick={() => onFilterChange('added')}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            filterStatus === 'added'
              ? 'bg-blue-600 text-white'
              : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          }`}
        >
          Added ({diffData.added.length})
        </button>
        <button
          onClick={() => onFilterChange('removed')}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            filterStatus === 'removed'
              ? 'bg-red-600 text-white'
              : 'bg-red-100 text-red-700 hover:bg-red-200'
          }`}
        >
          Removed ({diffData.removed.length})
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-gray-300">
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Function Name</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Similarity</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Changes</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredFunctions.map((func, idx) => (
              <tr key={idx} className={`border-b ${idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}>
                <td className="px-4 py-3 text-sm font-mono text-gray-900">{func.name}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={getStatusBadge(func.status)}>
                    {func.status.charAt(0).toUpperCase() + func.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  {func.similarity_score !== undefined ? (
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-2 bg-gray-200 rounded overflow-hidden">
                        <div
                          className={`h-full ${
                            func.similarity_score >= 95
                              ? 'bg-green-500'
                              : func.similarity_score >= 70
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${func.similarity_score}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">{func.similarity_score.toFixed(0)}%</span>
                    </div>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {func.change_count > 0 ? func.change_count + ' changes' : 'No changes'}
                </td>
                <td className="px-4 py-3 text-sm">
                  <button
                    onClick={() => onSelectFunction(func)}
                    className="text-indigo-600 hover:text-indigo-900 font-medium"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredFunctions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No functions match the selected filter.
        </div>
      )}
    </div>
  )
}
