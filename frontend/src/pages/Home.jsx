import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AIPanel from '../components/AIPanel';
import Editor from '../components/Editor';
import HistoryPanel from '../components/HistoryPanel';
import Navbar from '../components/Navbar';
import {
  completeCode,
  explainCode,
  fixCode,
  getErrorMessage,
  getHistory,
} from '../helpers/api';

const STARTER_SNIPPETS = {
  python: `def summarize_numbers(values):
    if not values:
        return 0
    total = sum(values)
    return total / len(values)
`,
  javascript: `function summarizeNumbers(values) {
  if (!values.length) {
    return 0;
  }

  const total = values.reduce((sum, value) => sum + value, 0);
  return total / values.length;
}
`,
  cpp: `#include <vector>
using namespace std;

double summarizeNumbers(const vector<int>& values) {
    if (values.empty()) {
        return 0;
    }

    int total = 0;
    for (int value : values) {
        total += value;
    }

    return static_cast<double>(total) / values.size();
}
`,
  java: `public class Summary {
    public static double summarizeNumbers(int[] values) {
        if (values.length == 0) {
            return 0;
        }

        int total = 0;
        for (int value : values) {
            total += value;
        }

        return (double) total / values.length;
    }
}
`,
  typescript: `function summarizeNumbers(values: number[]): number {
  if (!values.length) {
    return 0;
  }

  const total = values.reduce((sum, value) => sum + value, 0);
  return total / values.length;
}
`,
};

const ACTION_LABELS = {
  complete: 'Complete',
  fix: 'Fix bug',
  explain: 'Explain',
};

const HISTORY_ACTIONS = {
  completion: 'complete',
  fix: 'fix',
  explanation: 'explain',
};

export default function Home() {
  const navigate = useNavigate();
  const [code, setCode] = useState(STARTER_SNIPPETS.python);
  const [language, setLanguage] = useState('python');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeAction, setActiveAction] = useState('');
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleSessionExpired = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  }, [navigate]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError('');

    try {
      const response = await getHistory();
      setHistory(response.data.history || []);
    } catch (error) {
      if (error?.response?.status === 401) {
        handleSessionExpired();
        return;
      }

      setHistoryError(getErrorMessage(error, 'Could not load your recent sessions.'));
    } finally {
      setHistoryLoading(false);
    }
  }, [handleSessionExpired]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleAction = async (action) => {
    setActiveAction(action);
    setLoading(true);
    setCopied(false);
    setResult('');

    try {
      let response;

      if (action === 'complete') {
        response = await completeCode({ code, language });
      } else if (action === 'fix') {
        response = await fixCode({ code, language });
      } else {
        response = await explainCode({ code, language });
      }

      setResult(response.data.result);
      await loadHistory();
    } catch (error) {
      if (error?.response?.status === 401) {
        handleSessionExpired();
        return;
      }

      setResult(`Error: ${getErrorMessage(error, 'Something went wrong.')}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = (item) => {
    setCode(item.code || '');
    setLanguage(item.language || 'python');
    setResult(item.result || '');
    setActiveAction(HISTORY_ACTIONS[item.type] || '');
    setCopied(false);
  };

  const handleCopyResult = async () => {
    if (!result) {
      return;
    }

    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const lineCount = code ? code.split(/\r?\n/).length : 0;
  const charCount = code.length;

  return (
    <div className="workspace-shell">
      <Navbar />

      <main className="workspace-main">
        <section className="workspace-column workspace-column--main">
          <section className="hero-card">
            <div>
              <p className="eyebrow">Build faster with context-aware AI</p>
              <h2 className="hero-card__title">Write, debug, and explain code in one place.</h2>
              <p className="hero-card__copy">
                Switch between languages, call the assistant when you need help,
                and reopen recent sessions without leaving the editor.
              </p>
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <span className="hero-stat__label">Language</span>
                <strong>{language}</strong>
              </div>
              <div className="hero-stat">
                <span className="hero-stat__label">Lines</span>
                <strong>{lineCount}</strong>
              </div>
              <div className="hero-stat">
                <span className="hero-stat__label">Characters</span>
                <strong>{charCount}</strong>
              </div>
            </div>
          </section>

          <section className="panel-card">
            <div className="editor-toolbar">
              <div className="editor-toolbar__group">
                <label className="field-label" htmlFor="language-select">Language</label>
                <select
                  id="language-select"
                  className="field-input field-input--select"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="cpp">C++</option>
                  <option value="java">Java</option>
                  <option value="typescript">TypeScript</option>
                </select>
              </div>

              <div className="editor-toolbar__actions">
                <button
                  className="primary-btn"
                  type="button"
                  onClick={() => handleAction('complete')}
                  disabled={loading}
                >
                  {loading && activeAction === 'complete' ? 'Working...' : 'Complete'}
                </button>
                <button
                  className="accent-btn"
                  type="button"
                  onClick={() => handleAction('fix')}
                  disabled={loading}
                >
                  {loading && activeAction === 'fix' ? 'Working...' : 'Fix bug'}
                </button>
                <button
                  className="secondary-btn"
                  type="button"
                  onClick={() => handleAction('explain')}
                  disabled={loading}
                >
                  {loading && activeAction === 'explain' ? 'Working...' : 'Explain'}
                </button>
              </div>
            </div>

            <div className="editor-frame">
              <Editor code={code} setCode={setCode} language={language} />
            </div>

            <div className="editor-footer">
              <p className="muted-text">
                Current action:{' '}
                <strong>{ACTION_LABELS[activeAction] || 'Ready'}</strong>
              </p>
              <div className="editor-footer__actions">
                <button
                  className="ghost-btn"
                  type="button"
                  onClick={() => setCode(STARTER_SNIPPETS[language])}
                >
                  Load sample
                </button>
                <button
                  className="ghost-btn"
                  type="button"
                  onClick={() => {
                    setCode('');
                    setResult('');
                    setActiveAction('');
                    setCopied(false);
                  }}
                >
                  Clear editor
                </button>
              </div>
            </div>
          </section>
        </section>

        <aside className="workspace-column workspace-column--side">
          <AIPanel
            result={result}
            loading={loading}
            activeAction={activeAction}
            onCopy={handleCopyResult}
            copied={copied}
          />
          <HistoryPanel
            history={history}
            loading={historyLoading}
            error={historyError}
            onSelect={handleSelectHistory}
          />
        </aside>
      </main>
    </div>
  );
}
