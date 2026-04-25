const ACTION_LABELS = {
  complete: 'Code completion',
  fix: 'Bug fixing',
  explain: 'Code explanation',
};

export default function AIPanel({
  result,
  loading,
  activeAction,
  onCopy,
  copied,
}) {
  return (
    <section className="panel-card panel-card--stretch">
      <div className="panel-card__header">
        <div>
          <p className="eyebrow">Assistant output</p>
          <h2>AI Response</h2>
        </div>
        <button
          className="ghost-btn"
          type="button"
          onClick={onCopy}
          disabled={!result || loading}
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      {activeAction && (
        <p className="panel-tag">
          Last action: {ACTION_LABELS[activeAction] || 'AI task'}
        </p>
      )}

      {loading ? (
        <div className="state-box">
          <strong>Working on your request...</strong>
          <p>The assistant is generating a response for your latest code snippet.</p>
        </div>
      ) : result ? (
        <pre className="result-block">{result}</pre>
      ) : (
        <div className="state-box">
          <strong>Ready for your next prompt.</strong>
          <p>Try one of these actions:</p>
          <ul className="hint-list">
            <li>Complete unfinished code.</li>
            <li>Fix a bug and explain the root cause.</li>
            <li>Break down a complex snippet in plain language.</li>
          </ul>
        </div>
      )}
    </section>
  );
}
