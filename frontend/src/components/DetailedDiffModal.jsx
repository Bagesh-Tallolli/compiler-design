import React from 'react'

export default function DetailedDiffModal({ functionDiff, onClose }) {
  const hasInstructionChanges = functionDiff.instruction_changes && (
    functionDiff.instruction_changes.added.length > 0 ||
    functionDiff.instruction_changes.removed.length > 0 ||
    functionDiff.instruction_changes.modified.length > 0
  )

  const hasBlockChanges = functionDiff.block_changes && (
    functionDiff.block_changes.added.length > 0 ||
    functionDiff.block_changes.removed.length > 0
  )

  const hasCallChanges = functionDiff.call_changes && (
    functionDiff.call_changes.added.length > 0 ||
    functionDiff.call_changes.removed.length > 0
  )

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded shadow-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-gray-50 border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">{functionDiff.name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl font-bold">
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Summary */}
          <div className="bg-gray-50 p-4 rounded">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-600">Status</div>
                <div className="text-lg font-semibold text-gray-900 capitalize">{functionDiff.status}</div>
              </div>
              {functionDiff.similarity_score !== undefined && (
                <div>
                  <div className="text-sm text-gray-600">Similarity Score</div>
                  <div className="text-lg font-semibold text-gray-900">{functionDiff.similarity_score.toFixed(2)}%</div>
                </div>
              )}
              {functionDiff.change_count !== undefined && (
                <div>
                  <div className="text-sm text-gray-600">Total Changes</div>
                  <div className="text-lg font-semibold text-gray-900">{functionDiff.change_count}</div>
                </div>
              )}
            </div>
          </div>

          {/* Instruction Changes */}
          {hasInstructionChanges && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Instruction Changes</h3>

              {functionDiff.instruction_changes.added.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-green-700 mb-2">Added Instructions ({functionDiff.instruction_changes.added.length})</h4>
                  <div className="bg-green-50 border border-green-200 rounded p-3 space-y-1">
                    {functionDiff.instruction_changes.added.map((instr, idx) => (
                      <div key={idx} className="text-sm text-green-900 font-mono">
                        + {instr}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {functionDiff.instruction_changes.removed.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-700 mb-2">Removed Instructions ({functionDiff.instruction_changes.removed.length})</h4>
                  <div className="bg-red-50 border border-red-200 rounded p-3 space-y-1">
                    {functionDiff.instruction_changes.removed.map((instr, idx) => (
                      <div key={idx} className="text-sm text-red-900 font-mono">
                        - {instr}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {functionDiff.instruction_changes.modified.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-yellow-700 mb-2">Modified Instructions ({functionDiff.instruction_changes.modified.length})</h4>
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3 space-y-2">
                    {functionDiff.instruction_changes.modified.map((mod, idx) => (
                      <div key={idx} className="text-sm text-yellow-900">
                        <div className="font-mono">
                          - {mod.from}
                        </div>
                        <div className="font-mono">
                          + {mod.to}
                        </div>
                        <div className="text-xs text-yellow-700 mt-1">
                          Similarity: {(mod.similarity * 100).toFixed(0)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Block Changes */}
          {hasBlockChanges && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Basic Block Changes</h3>

              {functionDiff.block_changes.added.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-green-700 mb-2">Added Blocks ({functionDiff.block_changes.added.length})</h4>
                  <div className="bg-green-50 border border-green-200 rounded p-3 space-y-1">
                    {functionDiff.block_changes.added.map((block, idx) => (
                      <div key={idx} className="text-sm text-green-900 font-mono">
                        + {block}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {functionDiff.block_changes.removed.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-700 mb-2">Removed Blocks ({functionDiff.block_changes.removed.length})</h4>
                  <div className="bg-red-50 border border-red-200 rounded p-3 space-y-1">
                    {functionDiff.block_changes.removed.map((block, idx) => (
                      <div key={idx} className="text-sm text-red-900 font-mono">
                        - {block}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Call Changes */}
          {hasCallChanges && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Function Call Changes</h3>

              {functionDiff.call_changes.added.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-green-700 mb-2">Added Calls ({functionDiff.call_changes.added.length})</h4>
                  <div className="bg-green-50 border border-green-200 rounded p-3 space-y-1">
                    {functionDiff.call_changes.added.map((call, idx) => (
                      <div key={idx} className="text-sm text-green-900 font-mono">
                        + @{call}()
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {functionDiff.call_changes.removed.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-700 mb-2">Removed Calls ({functionDiff.call_changes.removed.length})</h4>
                  <div className="bg-red-50 border border-red-200 rounded p-3 space-y-1">
                    {functionDiff.call_changes.removed.map((call, idx) => (
                      <div key={idx} className="text-sm text-red-900 font-mono">
                        - @{call}()
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!hasInstructionChanges && !hasBlockChanges && !hasCallChanges && (
            <div className="bg-gray-50 p-4 rounded text-center text-gray-600">
              No structural changes detected.
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300 font-medium">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
