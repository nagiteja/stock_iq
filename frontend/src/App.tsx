import { useState } from "react";
import TickerForm from "./components/TickerForm";
import ReportView from "./components/ReportView";

const App = () => {
  const [report, setReport] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [scorecard, setScorecard] = useState<Record<string, unknown> | null>(null);
  const [compilerScorecard, setCompilerScorecard] = useState<Record<string, unknown> | null>(null);

  const handleAnalyze = async (ticker: string) => {
    setLoading(true);
    setError("");
    setReport("");
    setScorecard(null);
    setCompilerScorecard(null);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Analysis failed.");
      }
      const data = await response.json();
      setReport(data.report_markdown || "");
      setScorecard(data.scorecard || null);
      setCompilerScorecard(data.compiler_scorecard || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="header">
        <h1>StockIQ</h1>
        <p>Single-stock investor-style analysis.</p>
      </header>
      <section className="card">
        <TickerForm onAnalyze={handleAnalyze} loading={loading} />
        {loading && <div className="loading">Analyzing…</div>}
        {error && <div className="error">{error}</div>}
        {report && (
          <ReportView
            markdown={report}
            scorecard={scorecard}
            compilerScorecard={compilerScorecard}
          />
        )}
      </section>
    </div>
  );
};

export default App;
