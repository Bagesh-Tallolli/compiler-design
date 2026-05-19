import React from 'react'
import Editor from '@monaco-editor/react'

export default function EditorPane({ title, value, language = 'plaintext' }) {
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b bg-gray-50 text-sm font-medium">{title}</div>
      <div className="flex-1">
        <Editor height="100%" defaultLanguage={language} value={value} options={{ readOnly: true, minimap: { enabled: false } }} />
      </div>
    </div>
  )
}
