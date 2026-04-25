const TYPE_LABELS = {
  completion: 'Completion',
  fix: 'Bug fix',
  explanation: 'Explanation',
};

function formatDate(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Saved earlier';
  }

  return parsed.toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function buildSnippetPreview(code) {
  if (!code) {
    return 'No code preview available.';
  }

  return code.split(/\r?\n/).find((line) => line.trim())?.trim() || 'Empty snippet';
}

export default function HistoryPanel({
  history,
  loading,
  error,
  onSelect,
}) {
  return (
    <section className="panel-card panel-card--stretch">
      <div className="panel-card__header">
        <div>
          <p className="eyebrow">Saved context</p>
          <h2>Recent Sessions</h2>
        </div>
        <span className="history-count">{history.length} items</span>
      </div>

      {loading ? (
        <p className="muted-text">Loading recent AI sessions...</p>
      ) : error ? (
        <div className="state-box">
          <strong>History is unavailable.</strong>
          <p>{error}</p>
        </div>
      ) : history.length === 0 ? (
        <div className="state-box">
          <strong>No sessions yet.</strong>
          <p>Your recent completion, bug-fix, and explanation requests will appear here.</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item, index) => (
            <button
              key={`${item.created_at}-${index}`}
              className="history-item"
              type="button"
              onClick={() => onSelect(item)}
            >
              <div className="history-item__top">
                <span className="history-item__type">
                  {TYPE_LABELS[item.type] || 'AI action'}
                </span>
                <span className="history-item__date">{formatDate(item.created_at)}</span>
              </div>
              <p className="history-item__title">
                {item.language || 'Code snippet'}
              </p>
              <p className="history-item__preview">{buildSnippetPreview(item.code)}</p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
