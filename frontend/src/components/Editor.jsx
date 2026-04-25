import MonacoEditor from '@monaco-editor/react';

export default function Editor({ code, setCode, language }) {
  return (
    <MonacoEditor
      height="100%"
      language={language}
      value={code}
      onChange={(value) => setCode(value || '')}
      theme="vs-dark"
      options={{
        fontFamily: "'JetBrains Mono', 'Cascadia Code', Consolas, monospace",
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 18 },
        smoothScrolling: true,
      }}
    />
  );
}
