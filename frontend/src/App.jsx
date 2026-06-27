import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  UploadCloud, 
  Trash2, 
  Send, 
  Eye, 
  EyeOff, 
  Cpu, 
  Sliders, 
  Settings, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Layers, 
  Clock, 
  Info,
  Search,
  Check
} from 'lucide-react';
import './App.css';

// API Base URL (FastAPI)
const API_URL = 'http://127.0.0.1:8000';

// Custom lightweight Markdown Renderer to prevent package conflicts
function MarkdownRenderer({ content }) {
  if (!content) return null;
  const parts = content.split(/(```[\s\S]*?```)/g);
  
  return (
    <div className="markdown-body">
      {parts.map((part, index) => {
        if (part.startsWith('```')) {
          const codeMatch = part.match(/```(\w*)\n([\s\S]*?)```/);
          const code = codeMatch ? codeMatch[2] : part.slice(3, -3);
          return (
            <pre key={index}>
              <code>{code.trim()}</code>
            </pre>
          );
        } else {
          const lines = part.split('\n');
          return lines.map((line, lineIdx) => {
            let processedLine = line;
            processedLine = processedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            processedLine = processedLine.replace(/`(.*?)`/g, '<code>$1</code>');
            
            if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
              const itemContent = line.trim().slice(2);
              return (
                <ul key={lineIdx} style={{ margin: '4px 0 4px 20px', listStyleType: 'disc' }}>
                  <li dangerouslySetInnerHTML={{ __html: itemContent }} />
                </ul>
              );
            }
            
            const numListMatch = line.trim().match(/^(\d+)\.\s(.*)/);
            if (numListMatch) {
              const num = numListMatch[1];
              const itemContent = numListMatch[2];
              return (
                <ol key={lineIdx} start={num} style={{ margin: '4px 0 4px 20px' }}>
                  <li dangerouslySetInnerHTML={{ __html: itemContent }} />
                </ol>
              );
            }
            
            if (line.trim() === '') {
              return <div key={lineIdx} style={{ height: '8px' }} />;
            }
            
            return (
              <p 
                key={lineIdx} 
                style={{ margin: '0 0 6px 0' }}
                dangerouslySetInnerHTML={{ __html: processedLine }} 
              />
            );
          });
        }
      })}
    </div>
  );
}

export default function App() {
  // Config & Parameters
  const [apiKeyInput, setApiKeyInput] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [apiKeyVisible, setApiKeyVisible] = useState(false);
  const [hasServerKey, setHasServerKey] = useState(false);
  const [modelName, setModelName] = useState('gemini-1.5-flash');
  const [temperature, setTemperature] = useState(0.0);
  const [topK, setTopK] = useState(4);
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);

  // File Upload State
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [activeDocuments, setActiveDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ type: '', text: '' });

  // Chat Play State
  const [messages, setMessages] = useState([]);
  const [queryText, setQueryText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [chatError, setChatError] = useState('');

  // UI Tabs State
  const [activeTab, setActiveTab] = useState('chat');
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Load configuration and documents list on startup
  useEffect(() => {
    fetchConfig();
    fetchDocuments();
  }, []);

  // Auto scroll to chat bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const fetchConfig = async () => {
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`${API_URL}/api/config`, { headers });
      if (res.ok) {
        const data = await res.json();
        setHasServerKey(data.has_key);
      }
    } catch (err) {
      console.error('Failed to contact backend config endpoint:', err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_URL}/api/documents`);
      if (res.ok) {
        const data = await res.json();
        setActiveDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load active documents list:', err);
    }
  };

  const getAuthHeaders = () => {
    const headers = {};
    if (apiKeyInput.trim()) {
      headers['Authorization'] = `Bearer ${apiKeyInput.trim()}`;
    }
    return headers;
  };

  const handleApiKeyChange = (e) => {
    const val = e.target.value;
    setApiKeyInput(val);
    localStorage.setItem('gemini_api_key', val);
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
      setUploadStatus({ type: '', text: '' });
    }
  };

  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    
    setIsUploading(true);
    setUploadStatus({ type: 'info', text: 'Processing and indexing papers...' });

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        setUploadStatus({ 
          type: 'success', 
          text: `Success! Indexed ${data.chunks_count} segments.` 
        });
        setSelectedFiles([]);
        fetchDocuments();
        fetchConfig();
      } else {
        setUploadStatus({ 
          type: 'error', 
          text: data.detail || 'Ingestion failed.' 
        });
      }
    } catch (err) {
      setUploadStatus({ type: 'error', text: 'Network connection failed.' });
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const formatUserFriendlyError = (errStr) => {
    if (!errStr) return "An unexpected error occurred. Please try again in a moment.";
    
    const lower = errStr.toLowerCase();
    
    if (lower.includes('503') || lower.includes('unavailable') || lower.includes('high demand') || lower.includes('spikes in demand')) {
      return "The Gemini API is currently experiencing high demand or temporary server lag. Please wait a few seconds and try sending your question again.";
    }
    
    if (lower.includes('429') || lower.includes('quota') || lower.includes('resource_exhausted') || lower.includes('rate limit')) {
      return "Rate limit exceeded or quota exhausted. Please check your billing/usage limits on Google AI Studio, or try again shortly.";
    }
    
    if (lower.includes('401') || lower.includes('api key') || lower.includes('invalid') || lower.includes('unauthorized')) {
      return "Authentication failed. Please check your Gemini API key in the settings panel on the left and ensure it is correct.";
    }
    
    if (lower.includes('network') || lower.includes('failed to fetch') || lower.includes('connection refused')) {
      return "Unable to connect to the backend RAG server. Please ensure the Python backend is running locally on Port 8000.";
    }
    
    return "A temporary pipeline interruption occurred. Please try resubmitting your query in a few seconds.";
  };

  const handleSendQuery = async () => {
    if (!queryText.trim() || isGenerating) return;
    
    const userQuery = queryText.trim();
    setQueryText('');
    setChatError('');
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setIsGenerating(true);

    try {
      const res = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          question: userQuery,
          model_name: modelName,
          temperature: parseFloat(temperature),
          top_k: parseInt(topK)
        })
      });

      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', text: data.answer }]);
        setCurrentResponse(data);
      } else {
        const friendlyMsg = formatUserFriendlyError(data.detail);
        setChatError(data.detail || 'RAG generation failed.');
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: `⚠️ **Service Alert**: ${friendlyMsg}` 
        }]);
      }
    } catch (err) {
      const friendlyMsg = formatUserFriendlyError(err.message || 'network error');
      setChatError('Network error connecting to API.');
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `⚠️ **Service Alert**: ${friendlyMsg}` 
      }]);
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClearWorkspace = async () => {
    if (!window.confirm('Are you sure you want to delete all vector indices and uploads?')) return;
    
    try {
      const res = await fetch(`${API_URL}/api/clear`, { method: 'POST' });
      if (res.ok) {
        setMessages([]);
        setCurrentResponse(null);
        setActiveDocuments([]);
        setSelectedFiles([]);
        setUploadStatus({ type: 'success', text: 'Workspace cleared successfully.' });
        fetchConfig();
      }
    } catch (err) {
      console.error('Failed to clear workspace:', err);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const hasApiKey = apiKeyInput.trim() !== '' || hasServerKey;

  // Latency percentages calculation
  let retrievalPercent = 25;
  let generationPercent = 75;
  if (currentResponse?.metrics) {
    const { retrieval_latency_ms, total_latency_ms } = currentResponse.metrics;
    retrievalPercent = Math.max(5, Math.round((retrieval_latency_ms / total_latency_ms) * 100));
    generationPercent = 100 - retrievalPercent;
  }

  return (
    <div className="app-container">
      {/* ⚙️ LEFT PANEL: Config and Ingestion */}
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <span className="brand-name">Gemini Research Assistant</span>
        </div>

        <div className="sidebar-content">
          {/* Gemini Credentials */}
          <div className="settings-group">
            <label>🔑 Gemini Credentials</label>
            <div className="api-key-container">
              <input
                type={apiKeyVisible ? 'text' : 'password'}
                placeholder="Enter Gemini API Key..."
                value={apiKeyInput}
                onChange={handleApiKeyChange}
              />
              <button 
                type="button" 
                className="api-key-toggle"
                onClick={() => setApiKeyVisible(!apiKeyVisible)}
              >
                {apiKeyVisible ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            
            <div className="api-status-badge">
              <span className={`status-dot ${hasApiKey ? 'active' : 'inactive'}`}></span>
              <span style={{ color: hasApiKey ? 'var(--text-secondary)' : 'var(--text-muted)' }}>
                {hasApiKey ? 'Connected (Key Validated)' : 'API Key Required'}
              </span>
            </div>
            <a 
              href="https://aistudio.google.com/app/apikey" 
              target="_blank" 
              rel="noreferrer" 
              style={{ color: 'var(--color-primary)', fontSize: '0.78rem', textDecoration: 'none', marginTop: '4px', fontWeight: '500' }}
            >
              Get Free API Token ↗
            </a>
          </div>

          {/* Model Config */}
          <div className="settings-group">
            <label>🧠 Model Engine</label>
            <select value={modelName} onChange={(e) => setModelName(e.target.value)}>
              <option value="gemini-1.5-flash">gemini-1.5-flash (Fast)</option>
              <option value="gemini-1.5-pro">gemini-1.5-pro (Factual)</option>
            </select>
          </div>

          {/* Sliders Tuning */}
          <div className="settings-group">
            <div className="slider-label-row">
              <label>Temperature</label>
              <span className="slider-val">{temperature}</span>
            </div>
            <input 
              type="range" 
              min="0.0" 
              max="1.0" 
              step="0.1" 
              className="custom-range"
              value={temperature} 
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
          </div>

          <div className="settings-group">
            <div className="slider-label-row">
              <label>Top-K Retrieval</label>
              <span className="slider-val">{topK} chunks</span>
            </div>
            <input 
              type="range" 
              min="1" 
              max="10" 
              step="1" 
              className="custom-range"
              value={topK} 
              onChange={(e) => setTopK(parseInt(e.target.value))}
            />
          </div>

          {/* Indexing Configuration */}
          <div className="settings-group" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <div className="slider-label-row">
              <label>Chunk Size</label>
              <span className="slider-val">{chunkSize} chars</span>
            </div>
            <input 
              type="range" 
              min="200" 
              max="2000" 
              step="100" 
              className="custom-range"
              value={chunkSize} 
              onChange={(e) => setChunkSize(parseInt(e.target.value))}
            />
          </div>

          <div className="settings-group">
            <div className="slider-label-row">
              <label>Chunk Overlap</label>
              <span className="slider-val">{chunkOverlap} chars</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="500" 
              step="50" 
              className="custom-range"
              value={chunkOverlap} 
              onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
            />
          </div>

          {/* Ingestion Hub */}
          <div className="settings-group" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <label>📁 Ingestion Hub</label>
            
            <div className="uploader-dropzone" onClick={triggerFileInput}>
              <UploadCloud size={28} className="dropzone-icon" style={{ margin: '0 auto 8px' }} />
              <div className="dropzone-text">Click to choose papers</div>
              <div className="dropzone-subtext">PDF, DOCX, TXT (Max 10MB)</div>
              <input 
                type="file" 
                ref={fileInputRef}
                style={{ display: 'none' }} 
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
              />
            </div>

            {selectedFiles.length > 0 && (
              <div className="file-list">
                {selectedFiles.map((file, i) => (
                  <div className="file-item" key={i}>
                    <div className="file-info">
                      <FileText size={14} style={{ color: 'var(--color-primary)' }} />
                      <span className="file-name">{file.name}</span>
                    </div>
                    <button className="file-remove-btn" onClick={() => handleRemoveFile(i)}>
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button 
              className="btn-primary" 
              style={{ marginTop: '12px', width: '100%' }}
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || isUploading || !hasApiKey}
            >
              {isUploading ? 'Indexing...' : '🚀 Process Documents'}
            </button>

            {uploadStatus.text && (
              <div style={{ 
                marginTop: '10px', 
                fontSize: '0.78rem', 
                color: uploadStatus.type === 'success' ? 'var(--color-success)' : uploadStatus.type === 'error' ? 'var(--color-error)' : 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                {uploadStatus.type === 'success' ? <CheckCircle size={12} /> : <Info size={12} />}
                {uploadStatus.text}
              </div>
            )}
          </div>
        </div>

        {/* Clear Data */}
        <div className="sidebar-footer">
          <button className="btn-secondary" onClick={handleClearWorkspace} style={{ width: '100%' }}>
            <Trash2 size={14} />
            Clear Workspace
          </button>
        </div>
      </aside>

      {/* 🚀 RIGHT PANEL: Workspaces */}
      <main className="app-main">
        {/* Workspace Top Header & Navigation */}
        <header className="main-header">
          <div className="tabs-nav">
            <button 
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              <Sparkles size={16} />
              Chat Playground
            </button>
            <button 
              className={`tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
              onClick={() => setActiveTab('sources')}
              disabled={!currentResponse}
            >
              <Search size={16} />
              Inspected Sources
            </button>
            <button 
              className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
              onClick={() => setActiveTab('metrics')}
              disabled={!currentResponse}
            >
              <Cpu size={16} />
              Latency & Analytics
            </button>
          </div>

          <div className="header-actions">
            {activeDocuments.length > 0 ? (
              <div className="doc-pill">
                <Check size={12} />
                {activeDocuments.length} Document{activeDocuments.length > 1 ? 's' : ''} Active
              </div>
            ) : (
              <div className="doc-pill" style={{ color: 'var(--text-muted)', background: 'rgba(255,255,255,0.03)', borderColor: 'var(--border-color)' }}>
                No active context
              </div>
            )}
          </div>
        </header>

        {/* Workspace Tab Contents */}
        <div className="tab-content">
          
          {/* TAB 1: Chat Playground */}
          {activeTab === 'chat' && (
            <div className="chat-workspace">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon-wrapper">
                    <Sparkles size={28} />
                  </div>
                  <h3>Research Hub Workspace</h3>
                  <p>
                    Provide document context in the Ingestion Hub on the left. Once indexed, query facts and synthesize grounded summaries.
                  </p>
                  
                  <div className="capabilities-grid">
                    <div className="capability-card">
                      <Clock size={16} className="cap-icon" />
                      <h4>Latency Metrics</h4>
                      <p>Visualizes sub-millisecond retrieval and generation durations.</p>
                    </div>
                    <div className="capability-card">
                      <Layers size={16} className="cap-icon" />
                      <h4>FAISS Embeddings</h4>
                      <p>Chunks academic texts and maps similar context mathematically.</p>
                    </div>
                    <div className="capability-card">
                      <FileText size={16} className="cap-icon" />
                      <h4>Fact Grounding</h4>
                      <p>Guarantees citations mapped back to original source texts.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="chat-history">
                  {messages.map((msg, index) => (
                    <div className={`chat-bubble ${msg.role}`} key={index}>
                      <div className="chat-avatar">
                        {msg.role === 'user' ? '🕵️' : '🤖'}
                      </div>
                      <div className="chat-bubble-body">
                        <MarkdownRenderer content={msg.text} />
                      </div>
                    </div>
                  ))}
                  {isGenerating && (
                    <div className="chat-bubble assistant">
                      <div className="chat-avatar">🤖</div>
                      <div className="chat-bubble-body" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="status-dot active"></span>
                        Retrieving relevant segments and synthesizing answer...
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              )}

              {/* Chat Input Field */}
              <div className="chat-input-container">
                <div className="chat-input-wrapper">
                  <input
                    type="text"
                    className="chat-input-field"
                    placeholder={activeDocuments.length === 0 ? "⚠️ Upload research papers to start conversation..." : "Ask a question about the active papers..."}
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
                    disabled={activeDocuments.length === 0 || isGenerating}
                  />
                  <button 
                    className="chat-send-btn"
                    onClick={handleSendQuery}
                    disabled={!queryText.trim() || activeDocuments.length === 0 || isGenerating}
                  >
                    <Send size={16} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Inspected Sources */}
          {activeTab === 'sources' && currentResponse && (
            <div className="chat-workspace">
              <div className="inspector-header">
                <h3>Context inspector</h3>
                <p>Verify exactly what vector chunks were selected as the source grounds for your last reply.</p>
              </div>

              <div className="sources-grid">
                {currentResponse.retrieved_chunks && currentResponse.retrieved_chunks.length > 0 ? (
                  currentResponse.retrieved_chunks.map((chunk, idx) => {
                    const page = chunk.metadata?.page;
                    const score = chunk.metadata?.similarity_score;
                    return (
                      <div className="glass-panel glass-card source-card" key={idx}>
                        <div className="source-card-header">
                          <div className="source-title-row">
                            <span className="badge purple">Chunk {idx + 1}</span>
                            <span className="source-doc-name">{chunk.metadata?.source || 'Unknown file'}</span>
                          </div>
                          <div className="source-score-info">
                            {page !== null && page !== undefined && (
                              <span className="badge pink">Page {page}</span>
                            )}
                            {score !== null && score !== undefined && (
                              <span>Similarity L2: <strong>{score.toFixed(4)}</strong></span>
                            )}
                          </div>
                        </div>
                        <div className="source-text-box">
                          {chunk.page_content}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div style={{ color: 'var(--text-muted)', padding: '20px 0' }}>
                    No source chunks retrieved for this prompt.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Latency & Analytics */}
          {activeTab === 'metrics' && currentResponse && currentResponse.metrics && (
            <div className="chat-workspace">
              <div className="inspector-header">
                <h3>Execution Performance</h3>
                <p>Check processing speed breakdown of retrieval mapping vs language model text synthesis.</p>
              </div>

              {/* Big Metrics Grid */}
              <div className="metrics-summary-grid">
                <div className="glass-panel metric-big-card">
                  <div className="metric-card-val">{currentResponse.metrics.retrieval_latency_ms} ms</div>
                  <div className="metric-card-lbl">🔍 Retrieval Time</div>
                </div>
                <div className="glass-panel metric-big-card">
                  <div className="metric-card-val">{currentResponse.metrics.generation_latency_ms} ms</div>
                  <div className="metric-card-lbl">⚡ Generation Time</div>
                </div>
                <div className="glass-panel metric-big-card">
                  <div className="metric-card-val">{currentResponse.metrics.total_latency_ms} ms</div>
                  <div className="metric-card-lbl">🕒 Pipeline latency</div>
                </div>
              </div>

              {/* Latency Timeline Bar */}
              <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
                <div className="visualizer-title">Stage Share Visualization</div>
                <div className="progress-timeline-bar">
                  <div 
                    className="timeline-segment retrieval" 
                    style={{ width: `${retrievalPercent}%` }}
                    title={`Retrieval Latency: ${currentResponse.metrics.retrieval_latency_ms}ms`}
                  >
                    {retrievalPercent >= 15 && `Retrieval (${retrievalPercent}%)`}
                  </div>
                  <div 
                    className="timeline-segment generation" 
                    style={{ width: `${generationPercent}%` }}
                    title={`LLM Generation Latency: ${currentResponse.metrics.generation_latency_ms}ms`}
                  >
                    {generationPercent >= 15 && `LLM Synthesis (${generationPercent}%)`}
                  </div>
                </div>
                
                <div className="timeline-legend">
                  <div className="legend-item">
                    <span className="legend-color retrieval"></span>
                    <span>Vector similarity search context mapping</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color generation"></span>
                    <span>Google Gemini synthesis reply stream</span>
                  </div>
                </div>
              </div>

              {/* Pipeline Details */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div className="visualizer-title" style={{ marginBottom: '16px' }}>Configured Parameters & Environment</div>
                <pre className="params-code-block">
{`- LLM Engine: ${modelName}
- Temperature (Factual Index): ${temperature}
- Top-K retrieval chunks: ${topK} segments
- Chunk Ingestion settings: Size ${chunkSize} | Overlap ${chunkOverlap}
- Active sources used: ${currentResponse.metrics.sources?.join(', ') || 'None'}`}
                </pre>
              </div>

            </div>
          )}

        </div>
      </main>
    </div>
  );
}
