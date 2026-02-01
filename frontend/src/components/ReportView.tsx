import ReactMarkdown from "react-markdown";

type Scorecard = {
  score?: number;
  short_term?: string;
  mid_term?: string;
  long_term?: string;
  rationale?: string;
};

type CompilerScorecard = {
  final_score?: number;
  final_signal?: string;
  final_confidence?: number;
  top_reasons?: unknown[];
  key_risks?: unknown[];
  components?: {
    technical?: {
      signal?: string;
    };
    fundamental?: {
      signal?: string;
    };
  };
  weights?: {
    technical?: number;
    fundamental?: number;
  };
};

type Props = {
  markdown: string;
  scorecard: Scorecard | null;
  compilerScorecard: CompilerScorecard | null;
};

const ReportView = ({ markdown, scorecard, compilerScorecard }: Props) => {
  const score = scorecard?.score;
  const shortTerm = scorecard?.short_term;
  const midTerm = scorecard?.mid_term;
  const longTerm = scorecard?.long_term;
  const rationale = scorecard?.rationale;
  const compilerFinalScore = compilerScorecard?.final_score;
  const compilerFinalSignal = compilerScorecard?.final_signal;
  const compilerFinalConfidence = compilerScorecard?.final_confidence;
  const compilerTopReasons = compilerScorecard?.top_reasons;
  const compilerKeyRisks = compilerScorecard?.key_risks;
  const compilerComponents = compilerScorecard?.components;
  const compilerWeights = compilerScorecard?.weights;

  return (
    <div className="report">
      {scorecard && (
        <div className="scorecard">
          <h2>Scorecard</h2>
          <div className="scorecard-grid">
            <div>
              <span className="label">Score</span>
              <span className="value">{typeof score === "number" ? score : "N/A"}</span>
            </div>
            <div>
              <span className="label">Short Term</span>
              <span className="value">{typeof shortTerm === "string" ? shortTerm : "N/A"}</span>
            </div>
            <div>
              <span className="label">Mid Term</span>
              <span className="value">{typeof midTerm === "string" ? midTerm : "N/A"}</span>
            </div>
            <div>
              <span className="label">Long Term</span>
              <span className="value">{typeof longTerm === "string" ? longTerm : "N/A"}</span>
            </div>
          </div>
          {typeof rationale === "string" && (
            <p className="scorecard-note">{rationale}</p>
          )}
        </div>
      )}
      {compilerScorecard && (
        <div className="scorecard">
          <h2>Technical+Fundamental Scorecard</h2>
          <div className="scorecard-grid">
            <div>
              <span className="label">Final Score</span>
              <span className="value">
                {typeof compilerFinalScore === "number" ? compilerFinalScore : "N/A"}
              </span>
            </div>
            <div>
              <span className="label">Signal</span>
              <span className="value">
                {typeof compilerFinalSignal === "string"
                  ? compilerFinalSignal.toUpperCase()
                  : "N/A"}
              </span>
            </div>
            <div>
              <span className="label">Confidence</span>
              <span className="value">
                {typeof compilerFinalConfidence === "number"
                  ? compilerFinalConfidence.toFixed(2)
                  : "N/A"}
              </span>
            </div>
          </div>
          <div className="scorecard-grid">
            <div>
              <span className="label">Technical Weight</span>
              <span className="value">
                {typeof compilerWeights?.technical === "number"
                  ? compilerWeights.technical.toFixed(2)
                  : "N/A"}
              </span>
            </div>
            <div>
              <span className="label">Fundamental Weight</span>
              <span className="value">
                {typeof compilerWeights?.fundamental === "number"
                  ? compilerWeights.fundamental.toFixed(2)
                  : "N/A"}
              </span>
            </div>
          </div>
          <div className="scorecard-grid">
            <div>
              <span className="label">Technical Signal</span>
              <span className="value">
                {typeof compilerComponents?.technical?.signal === "string"
                  ? compilerComponents.technical.signal.toUpperCase()
                  : "N/A"}
              </span>
            </div>
            <div>
              <span className="label">Fundamental Signal</span>
              <span className="value">
                {typeof compilerComponents?.fundamental?.signal === "string"
                  ? compilerComponents.fundamental.signal.toUpperCase()
                  : "N/A"}
              </span>
            </div>
          </div>
          {Array.isArray(compilerTopReasons) && compilerTopReasons.length > 0 && (
            <div>
              <span className="label">Top Reasons</span>
              <ul className="scorecard-list">
                {compilerTopReasons.map((reason, index) => (
                  <li key={`reason-${index}`}>{String(reason)}</li>
                ))}
              </ul>
            </div>
          )}
          {Array.isArray(compilerKeyRisks) && compilerKeyRisks.length > 0 && (
            <div>
              <span className="label">Key Risks</span>
              <ul className="scorecard-list">
                {compilerKeyRisks.map((risk, index) => (
                  <li key={`risk-${index}`}>{String(risk)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      <ReactMarkdown>{markdown}</ReactMarkdown>
    </div>
  );
};

export default ReportView;
