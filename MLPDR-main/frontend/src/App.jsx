import { useMemo, useState } from "react";

const OCR_MODES = {
  trained: "Moroccan Plate (Custom OCR)",
  tesseract: "General Plate (Tesseract-OCR)",
};

function App() {
  const [file, setFile] = useState(null);
  const [ocrMode, setOcrMode] = useState("trained");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [response, setResponse] = useState(null);

  const previewUrl = useMemo(() => {
    if (!file) return "";
    return URL.createObjectURL(file);
  }, [file]);

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0];
    setResponse(null);
    setError("");
    setFile(selected || null);
  };

  const onDrop = (event) => {
    event.preventDefault();
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) {
      setResponse(null);
      setError("");
      setFile(dropped);
    }
  };

  const onDragOver = (event) => {
    event.preventDefault();
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError("Select an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const body = new FormData();
      body.append("image", file);
      body.append("ocr_mode", ocrMode);

      const res = await fetch("/api/upload", {
        method: "POST",
        body,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Upload failed.");
      }

      const artifacts = data.artifacts || {};
      setResponse({
        ...data,
        artifacts: {
          input: artifacts.input ? `/api${artifacts.input}` : "",
          detection: artifacts.detection ? `/api${artifacts.detection}` : "",
          plate: artifacts.plate ? `/api${artifacts.plate}` : "",
          segmented: artifacts.segmented ? `/api${artifacts.segmented}` : "",
        },
      });
    } catch (err) {
      setError(err.message || "Unexpected error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">MLPDR</p>
        <h1>Moroccan Plate Detection & Recognition</h1>
        <p className="subtitle">Same model logic, cleaner web interface in React.</p>
      </header>

      <main className="layout">
        <section className="card upload-card">
          <h2>Upload</h2>
          <form onSubmit={submit}>
            <div className="mode-grid">
              {Object.entries(OCR_MODES).map(([value, label]) => (
                <label key={value} className={`mode ${ocrMode === value ? "active" : ""}`}>
                  <input
                    type="radio"
                    name="ocr_mode"
                    value={value}
                    checked={ocrMode === value}
                    onChange={(e) => setOcrMode(e.target.value)}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>

            <label className="dropzone" onDrop={onDrop} onDragOver={onDragOver}>
              <input type="file" accept="image/*" onChange={handleFileChange} />
              <span>{file ? file.name : "Drop image here or click to browse"}</span>
            </label>

            <button type="submit" disabled={loading}>
              {loading ? "Processing..." : "Detect Plate"}
            </button>
          </form>

          {error && <p className="error">{error}</p>}

          {previewUrl && (
            <div className="preview-box">
              <p>Input preview</p>
              <img src={previewUrl} alt="Selected" />
            </div>
          )}
        </section>

        <section className="card result-card">
          <h2>Result</h2>
          {!response && <p className="placeholder">No result yet.</p>}

          {response && (
            <>
              <div className="result-head">
                <div>
                  <p className="label">OCR mode</p>
                  <p>{response.ocr_mode}</p>
                </div>
                <div>
                  <p className="label">Plate detected</p>
                  <p>{response.has_plate ? "Yes" : "No"}</p>
                </div>
              </div>

              <div className="plate-output">
                <p className="label">Recognized plate</p>
                <p className="plate-text">{response.plate_text || "-"}</p>
              </div>

              <div className="artifacts-grid">
                {response.artifacts.detection && (
                  <figure>
                    <figcaption>Detection</figcaption>
                    <img src={response.artifacts.detection} alt="Detection" />
                  </figure>
                )}

                {response.artifacts.plate && (
                  <figure>
                    <figcaption>Plate crop</figcaption>
                    <img src={response.artifacts.plate} alt="Plate" />
                  </figure>
                )}

                {response.artifacts.segmented && (
                  <figure>
                    <figcaption>Segmented chars</figcaption>
                    <img src={response.artifacts.segmented} alt="Segmented" />
                  </figure>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
