import React, { useState } from 'react';
import axios from 'axios';

export default function TestCodeEditor() {
  const [oldCode, setOldCode] = useState('');
  const [newCode, setNewCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!oldCode || !newCode) {
      setError('Please provide both old and new source code.');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const form = new FormData();
      const oldBlob = new Blob([oldCode], { type: 'text/plain' });
      const newBlob = new Blob([newCode], { type: 'text/plain' });
      const oldFile = new File([oldBlob], 'old.cpp');
      const newFile = new File([newBlob], 'new.cpp');
      form.append('old_file', oldFile);
      form.append('new_file', newFile);

      const resp = await axios.post('http://localhost:8000/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      if (resp.data && resp.data.success) {
        setResult(resp.data);
      } else {
        setError(resp.data?.error || 'Unexpected response from server');
      }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e.message;
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!result || !result.report_text) return;
    const blob = new Blob([result.report_text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'semantic_report.txt';
    a.click();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-slate-200">Manual Code Test</h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <textarea
          className="w-full h-64 p-2 rounded bg-slate-800 text-slate-200 focus:outline-none"
          placeholder="Old source code"
          value={oldCode}
          onChange={(e) => setOldCode(e.target.value)}
        />
        <textarea
          className="w-full h-64 p-2 rounded bg-slate-800 text-slate-200 focus:outline-none"
          placeholder="New source code"
          value={newCode}
          onChange={(e) => setNewCode(e.target.value)}
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50"
      >
        {loading ? 'Analyzing…' : 'Run Analysis'}
      </button>

      {error && (
        <div className="mt-4 p-2 bg-red-900 text-red-200 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6">
          <button
            onClick={downloadReport}
            className="mb-2 px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded"
          >Download Report</button>
          <div className="p-4 bg-slate-800 rounded text-slate-200 overflow-auto max-h-96">
            <pre>{result.report_text || JSON.stringify(result, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
