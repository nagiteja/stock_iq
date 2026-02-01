import { useState } from "react";

type Props = {
  onAnalyze: (ticker: string) => void;
  loading: boolean;
};

const TickerForm = ({ onAnalyze, loading }: Props) => {
  const [ticker, setTicker] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!ticker.trim()) {
      return;
    }
    onAnalyze(ticker.trim().toUpperCase());
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label htmlFor="ticker">Ticker</label>
      <div className="form-row">
        <input
          id="ticker"
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          placeholder="AAPL"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          Analyze
        </button>
      </div>
    </form>
  );
};

export default TickerForm;
