import React from 'react'

export default function TabSelector({ tab, setTab }) {
  return (
    <div className="bg-white rounded shadow">
      <div className="flex border-b">
        <button
          onClick={() => setTab('raw')}
          className={`flex-1 px-4 py-3 text-center font-medium transition ${
            tab === 'raw'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Raw LLVM IR
        </button>
        <button
          onClick={() => setTab('normalized')}
          className={`flex-1 px-4 py-3 text-center font-medium transition ${
            tab === 'normalized'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Normalized LLVM IR
        </button>
      </div>
    </div>
  )
}
