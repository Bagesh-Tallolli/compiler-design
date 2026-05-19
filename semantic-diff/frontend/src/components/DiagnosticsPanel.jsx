import React from 'react'

export default function DiagnosticsPanel({ diagnostics }) {
  const oldDiag = diagnostics.old || {}
  const newDiag = diagnostics.new || {}

  const statItem = (label, value) => (
    <div className="flex justify-between items-center py-2 border-b last:border-b-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-mono font-semibold text-indigo-600">{value}</span>
    </div>
  )

  return (
    <div className="bg-white rounded shadow p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Normalization Diagnostics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium text-gray-700 mb-3">Old File</h4>
          <div className="bg-gray-50 p-3 rounded">
            {statItem('Metadata Removed', oldDiag.metadata_removed || 0)}
            {statItem('Variables Canonicalized', oldDiag.variables_canonicalized || 0)}
            {statItem('Blocks Normalized', oldDiag.blocks_normalized || 0)}
            {statItem('Comments Removed', oldDiag.comments_removed || 0)}
          </div>
        </div>
        <div>
          <h4 className="font-medium text-gray-700 mb-3">New File</h4>
          <div className="bg-gray-50 p-3 rounded">
            {statItem('Metadata Removed', newDiag.metadata_removed || 0)}
            {statItem('Variables Canonicalized', newDiag.variables_canonicalized || 0)}
            {statItem('Blocks Normalized', newDiag.blocks_normalized || 0)}
            {statItem('Comments Removed', newDiag.comments_removed || 0)}
          </div>
        </div>
      </div>
    </div>
  )
}
