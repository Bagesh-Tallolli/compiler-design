import React, { useState } from 'react'
import axios from 'axios'
import EditorPane from './components/EditorPane'
import TabSelector from './components/TabSelector'
import DiagnosticsPanel from './components/DiagnosticsPanel'
import FunctionDiffTable from './components/FunctionDiffTable'
import DetailedDiffModal from './components/DetailedDiffModal'
import CFGAnalysisPanel from './components/CFGAnalysisPanel'
import DFGSemanticPanel from './components/DFGSemanticPanel'

export default function App() {
  const [oldFile, setOldFile] = useState(null)
  const [newFile, setNewFile] = useState(null)
  const [oldIR, setOldIR] = useState('')
  const [newIR, setNewIR] = useState('')
  const [normalizedOldIR, setNormalizedOldIR] = useState('')
  const [normalizedNewIR, setNormalizedNewIR] = useState('')
  const [loading, setLoading] = useState(false)
  const [alert, setAlert] = useState(null)
  const [tab, setTab] = useState('raw')
  const [diagnostics, setDiagnostics] = useState(null)
  const [diffData, setDiffData] = useState(null)
  const [cfgData, setCFGData] = useState(null)
  const [dfgData, setDFGData] = useState(null)
  const [selectedFunction, setSelectedFunction] = useState(null)
  const [filterStatus, setFilterStatus] = useState('all')

  const handleGenerate = async () => {
    if (!oldFile || !newFile) {
      setAlert({ type: 'error', msg: 'Please select both old and new source files.' })
      return
    }

    const form = new FormData()
    form.append('old_file', oldFile)
    form.append('new_file', newFile)

    try {
      setLoading(true)
      setAlert(null)
      setDiagnostics(null)
      setDiffData(null)
      setCFGData(null)
      setDFGData(null)
      const resp = await axios.post('http://localhost:8000/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })

      if (resp.data && resp.data.success) {
        setOldIR(resp.data.old_ir)
        setNewIR(resp.data.new_ir)
        setNormalizedOldIR(resp.data.normalized_old_ir)
        setNormalizedNewIR(resp.data.normalized_new_ir)
        setDiagnostics(resp.data.diagnostics)
        setDiffData(resp.data.diff)
        setCFGData(resp.data.cfg_analysis)
        setDFGData(resp.data.dfg_analysis)
        setTab('raw')
        setFilterStatus('all')
        setAlert({ type: 'success', msg: 'LLVM IR generated, normalized, diffed, and analyzed successfully.' })
      } else {
        setAlert({ type: 'error', msg: resp.data.error || 'Unexpected response' })
      }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e.message
      setAlert({ type: 'error', msg })
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadDiff = () => {
    if (!diffData) return
    const dataStr = JSON.stringify(diffData, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `semantic-diff-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleDownloadCFG = () => {
    if (!cfgData) return
    const dataStr = JSON.stringify(cfgData, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cfg-analysis-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleDownloadDFG = () => {
    if (!dfgData) return
    const dataStr = JSON.stringify(dfgData, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dfg-analysis-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const currentOldIR = tab === 'raw' ? oldIR : normalizedOldIR
  const currentNewIR = tab === 'raw' ? newIR : normalizedNewIR

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Semantic Diff for Compiler IR</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Upload Old Source File</label>
                <input type="file" accept=".c,.cpp" onChange={(e) => setOldFile(e.target.files[0])} className="mt-2" />
                {oldFile && <div className="mt-2 text-sm text-gray-600">{oldFile.name}</div>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Upload New Source File</label>
                <input type="file" accept=".c,.cpp" onChange={(e) => setNewFile(e.target.files[0])} className="mt-2" />
                {newFile && <div className="mt-2 text-sm text-gray-600">{newFile.name}</div>}
              </div>
            </div>

            <div className="mt-6 flex items-center space-x-4">
              <button onClick={handleGenerate} disabled={loading} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60">
                {loading ? 'Analyzing...' : 'Generate & Analyze'}
              </button>
              {alert && (
                <div className={`px-3 py-2 rounded text-sm ${alert.type === 'error' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {alert.msg}
                </div>
              )}
            </div>
          </div>

          {diagnostics && (
            <DiagnosticsPanel diagnostics={diagnostics} />
          )}

          {diffData && (
            <FunctionDiffTable 
              diffData={diffData}
              onSelectFunction={setSelectedFunction}
              filterStatus={filterStatus}
              onFilterChange={setFilterStatus}
              onDownloadDiff={handleDownloadDiff}
            />
          )}

          {cfgData && cfgData.length > 0 && (
            <CFGAnalysisPanel 
              cfgData={cfgData}
              onDownloadCFG={handleDownloadCFG}
            />
          )}

          {dfgData && dfgData.length > 0 && (
            <DFGSemanticPanel
              dfgData={dfgData}
              onDownloadDFG={handleDownloadDFG}
            />
          )}

          {(oldIR || newIR) && (
            <>
              <TabSelector tab={tab} setTab={setTab} />
              <div className="bg-white p-4 rounded shadow">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[70vh]">
                  <EditorPane title={`${tab === 'raw' ? 'Raw' : 'Normalized'} Old LLVM IR`} value={currentOldIR} language="llvm" />
                  <EditorPane title={`${tab === 'raw' ? 'Raw' : 'Normalized'} New LLVM IR`} value={currentNewIR} language="llvm" />
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      {selectedFunction && (
        <DetailedDiffModal
          functionDiff={selectedFunction}
          onClose={() => setSelectedFunction(null)}
        />
      )}
    </div>
  )
}
