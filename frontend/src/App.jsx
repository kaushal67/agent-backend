import { useEffect, useState } from "react";
import { askTriageImage, askTriageQuestion, fetchQueryHistory } from "./api";

const quickPrompts = [
  "My tomato leaves have yellow spots. What should I do?",
  "Will heavy rain in Pune affect my wheat crop this week?",
  "Any subsidy schemes available for drip irrigation in Maharashtra?",
  "Rice plants are wilting after high heat. How urgent is this?"
];

function humanizeKey(value) {
  return value.replace(/_/g, " ");
}

function App() {
  const [message, setMessage] = useState("");
  const [imageNote, setImageNote] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [savedQueries, setSavedQueries] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    loadSavedQueries();
  }, []);

  const loadSavedQueries = async () => {
    setIsHistoryLoading(true);
    setHistoryError("");

    try {
      const payload = await fetchQueryHistory(20);
      setSavedQueries(payload.items || []);
    } catch (error) {
      setHistoryError(error.message || "Could not load saved queries.");
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const runRequest = async (source, requestAction, questionLabel) => {
    const cleaned = questionLabel.trim();
    if (!cleaned) return;

    const requestId = typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`;

    setIsLoading(true);
    setHistory((prev) => [
      {
        id: requestId,
        question: questionLabel,
        source,
        status: "loading"
      },
      ...prev
    ]);

    try {
      const result = await requestAction(cleaned);
      setHistory((prev) =>
        prev.map((item) =>
          item.id === requestId
            ? {
                ...item,
                status: "done",
                result
              }
            : item
        )
      );
      await loadSavedQueries();
    } catch (error) {
      setHistory((prev) =>
        prev.map((item) =>
          item.id === requestId
            ? {
                ...item,
                status: "error",
                error: error.message || "Request failed."
              }
            : item
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const submitQuestion = async (question) => {
    const cleaned = question.trim();
    if (!cleaned) return;
    setMessage("");
    await runRequest("text", () => askTriageQuestion(cleaned), cleaned);
  };

  const submitImageQuestion = async (event) => {
    event.preventDefault();
    if (!imageFile) return;

    const displayText = imageNote.trim()
      ? `Image triage: ${imageNote.trim()}`
      : `Image triage: ${imageFile.name}`;

    const selectedFile = imageFile;
    const selectedNote = imageNote;

    setImageFile(null);
    setImageNote("");
    setFileInputKey((prev) => prev + 1);

    await runRequest(
      "image",
      () => askTriageImage(selectedFile, selectedNote),
      displayText
    );
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    await submitQuestion(message);
  };

  return (
    <div className="app-shell">
      <div className="grain-overlay" />
      <main className="layout">
        <section className="hero">
          <p className="eyebrow">Agri Support Console</p>
          <h1>Crop Triage Assistant</h1>
          <p className="subtitle">
            Classify issue urgency, detect entities, and get actionable farmer guidance.
          </p>
        </section>

        <section className="ask-panel">
          <div className="ask-grid">
            <form onSubmit={onSubmit} className="ask-form">
              <label htmlFor="question">Describe your agriculture issue</label>
              <textarea
                id="question"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Example: Brown patches appeared on my cotton leaves after rain."
                rows={4}
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !message.trim()}>
                {isLoading ? "Analyzing..." : "Run Text Triage"}
              </button>
            </form>

            <form onSubmit={submitImageQuestion} className="ask-form image-form">
              <label htmlFor="imageUpload">Upload crop image (JPG, PNG, WEBP)</label>
              <input
                key={fileInputKey}
                id="imageUpload"
                type="file"
                accept="image/*"
                onChange={(event) => setImageFile(event.target.files?.[0] || null)}
                disabled={isLoading}
              />
              <textarea
                id="imageNote"
                value={imageNote}
                onChange={(event) => setImageNote(event.target.value)}
                placeholder="Optional note: e.g. leaf rust-like yellow streaks in wheat"
                rows={3}
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !imageFile}>
                {isLoading ? "Analyzing..." : "Run Image Triage"}
              </button>
            </form>
          </div>

          <div className="prompt-list">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                className="prompt-chip"
                type="button"
                onClick={() => submitQuestion(prompt)}
                disabled={isLoading}
              >
                {prompt}
              </button>
            ))}
          </div>
        </section>

        <section className="results-panel">
          <h2>Triage Results</h2>

          {history.length === 0 ? (
            <div className="empty-state">
              <p>No triage requests yet.</p>
              <p>Submit a question to see classification, entities, and final response.</p>
            </div>
          ) : (
            history.map((item) => {
              const result = item.result || {};
              const classification = result.classification || {};
              const entities = result.entities || {};
              const entityRows = Object.entries(entities).filter(([, value]) => Boolean(value));

              return (
                <article className="result-card" key={item.id}>
                  <p className="question-label">Farmer Query</p>
                  <p className="question-text">{item.question}</p>
                  <p className="source-tag">
                    Source: {item.source === "image" ? "image upload" : "text input"}
                  </p>

                  {item.status === "loading" && <p className="status">Triage in progress...</p>}
                  {item.status === "error" && <p className="status error">{item.error}</p>}

                  {item.status === "done" && (
                    <>
                      <div className="meta-row">
                        <span className="meta-pill">
                          Intent: {classification.intent || "unknown"}
                        </span>
                        <span className="meta-pill">
                          Urgency: {classification.urgency || "unknown"}
                        </span>
                        <span className="meta-pill">Record ID: {result.db_id}</span>
                        {result.image?.filename && (
                          <span className="meta-pill">Image: {result.image.filename}</span>
                        )}
                      </div>

                      <div className="entity-box">
                        <p className="entity-title">Extracted Entities</p>
                        {entityRows.length === 0 ? (
                          <p className="entity-empty">No entities extracted.</p>
                        ) : (
                          <ul>
                            {entityRows.map(([key, value]) => (
                              <li key={key}>
                                <strong>{humanizeKey(key)}:</strong> {value}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      <div className="answer-box">
                        <p className="answer-title">System Response</p>
                        <pre>{result.answer || "No answer generated."}</pre>
                      </div>
                    </>
                  )}
                </article>
              );
            })
          )}

          <div className="saved-header">
            <h3>Saved Queries (Database)</h3>
            <button type="button" onClick={loadSavedQueries} disabled={isHistoryLoading}>
              {isHistoryLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {historyError && <p className="status error">{historyError}</p>}

          {savedQueries.length === 0 ? (
            <div className="empty-state">
              <p>No saved queries yet.</p>
            </div>
          ) : (
            savedQueries.map((entry) => (
              <article className="saved-card" key={entry.id}>
                <p className="question-label">Record #{entry.id}</p>
                <p className="question-text">{entry.query}</p>
                <div className="meta-row">
                  <span className="meta-pill">Intent: {entry.intent || "unknown"}</span>
                  <span className="meta-pill">Urgency: {entry.urgency || "unknown"}</span>
                </div>
                <div className="answer-box">
                  <p className="answer-title">Stored Response</p>
                  <pre>{entry.response || "No stored response."}</pre>
                </div>
              </article>
            ))
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
