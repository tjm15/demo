import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Settings, Sparkles, MapPin, X, Zap, Shield, ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { PanelHost } from './PanelHost';
import { ErrorBoundary } from './ErrorBoundary';
import { RunControls } from './RunControls';
import { useReasoningStream } from '../../hooks/useReasoningStream';

type Module = 'evidence' | 'policy' | 'strategy' | 'vision' | 'feedback' | 'dm';

const MODULES: { id: Module; label: string; description: string; icon: string }[] = [
  { id: 'evidence', label: 'Evidence Base', description: 'Build your foundation by exploring geospatial data and querying a vast library of planning documents.', icon: '🗺️' },
  { id: 'vision', label: 'Vision & Concepts', description: 'Translate data and policy into compelling visuals. Generate high-quality architectural and landscape imagery.', icon: '🎨' },
  { id: 'policy', label: 'Policy Drafter', description: 'Draft, refine, and validate planning policy. Research, check for national compliance, and get editing suggestions.', icon: '📋' },
  { id: 'strategy', label: 'Strategy Modeler', description: 'Explore the future impact of high-level strategies. Model and compare complex scenarios for informed decisions.', icon: '📊' },
  { id: 'dm', label: 'Site Assessment', description: 'Conduct detailed, map-based site assessments. Generate grounded reports for any location or uploaded site data.', icon: '📍' },
  { id: 'feedback', label: 'Feedback Analysis', description: 'Instantly synthesize public and stakeholder feedback. Analyze unstructured text to find actionable insights.', icon: '💬' },
];

const EXAMPLE_PROMPTS: Record<Module, string[]> = {
  dm: [
    '45 unit residential development, 6 storeys, near conservation area',
    'Change of use from office to 12 residential flats',
  ],
  evidence: [
    'Site at 51.5074, -0.1278 for residential development',
    'Brownfield site near town center, assess constraints'
  ],
  policy: [
    'Review housing policy H1 for consistency with London Plan',
    'Draft policy for sustainable transport in new developments'
  ],
  strategy: [
    'Compare urban extension vs brownfield intensification for 5000 homes',
    'Assess town centre regeneration options'
  ],
  vision: [
    'Check design compliance for 8-storey mixed-use scheme',
    'Review facade materials for conservation area development'
  ],
  feedback: [
    'Analyze consultation responses on proposed local plan',
    'Identify themes from 200+ objections to housing allocation'
  ],
};

export function AppWorkspace() {
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [prompt, setPrompt] = useState('');
  const [runMode, setRunMode] = useState<'stable' | 'deep'>('stable');
  const [allowWebFetch, setAllowWebFetch] = useState(false);
  const [showSiteInput, setShowSiteInput] = useState(false);
  const [lat, setLat] = useState<string>('');
  const [lng, setLng] = useState<string>('');
  const [showSettings, setShowSettings] = useState(false);
  // Landing-page quick question (auto-classified)
  const [askText, setAskText] = useState('');
  
  const { panels, isRunning, startReasoning, reasoning } = useReasoningStream();

  const handleModuleSelect = (moduleId: Module) => {
    setSelectedModule(moduleId);
  };

  const handleBack = () => {
    setSelectedModule(null);
    setPrompt('');
    setLat('');
    setLng('');
    setShowSiteInput(false);
  };

  // Heuristic auto-classifier to route question to the best module
  const classifyQuestion = (text: string): Module => {
    const t = text.toLowerCase();
    const score: Record<Module, number> = { evidence: 0, policy: 0, strategy: 0, vision: 0, feedback: 0, dm: 0 };
    const bump = (m: Module, n = 1) => (score[m] += n);
    if (/\b(lat|latitude)[^\d-]*[-+]?\d|\b(lon|lng|longitude)[^\d-]*[-+]?\d/.test(t)) { bump('evidence', 2); bump('dm', 2); }
    if (/(site|parcel|plot|map|constraints|flood|heritage|conservation|brownfield)/.test(t)) { bump('evidence', 2); bump('dm', 1); }
    if (/(units|storeys|stories|dwellings|application|app ref|planning ref)/.test(t)) { bump('dm', 2); }
    if (/(policy|draft|wording|criterion|compliance|soundness|h\d+\.?\d*|london plan|nppf|npff)/.test(t)) { bump('policy', 3); }
    if (/(scenario|compare|vs\.|versus|option|model|impact|capacity|5000 homes|targets|trajectory)/.test(t)) { bump('strategy', 3); }
    if (/(render|visual|concept|design|façade|facade|materials|mass\b|elevation|streetscape|illustration)/.test(t)) { bump('vision', 3); }
    if (/(consultation|responses|objections|themes|survey|sentiment|feedback|comments)/.test(t)) { bump('feedback', 3); }
    if (/(where|what|show|find|nearby|around)/.test(t)) bump('evidence', 1);
    const order: Module[] = ['dm', 'evidence', 'policy', 'strategy', 'feedback', 'vision'];
    let best: Module = 'evidence'; let bestScore = -Infinity;
    for (const m of order) { if (score[m] > bestScore) { best = m; bestScore = score[m]; } }
    return best;
  };

  const parseCoords = (text: string): { lat: number; lng: number } | undefined => {
    const match = text.match(/([-+]?\d{1,2}\.\d+)\s*,\s*([-+]?\d{1,3}\.\d+)/);
    if (!match) return undefined;
    const latVal = parseFloat(match[1]);
    const lngVal = parseFloat(match[2]);
    if (isFinite(latVal) && isFinite(lngVal)) return { lat: latVal, lng: lngVal };
    return undefined;
  };

  const handleAsk = () => {
    const q = askText.trim();
    if (!q || isRunning) return;
    const autoModule = classifyQuestion(q);
    const coords = parseCoords(q);
    setSelectedModule(autoModule);
    setPrompt(q);
    startReasoning({
      module: autoModule,
      prompt: q,
      run_mode: runMode,
      allow_web_fetch: allowWebFetch,
      site_data: (autoModule === 'evidence' || autoModule === 'dm') && coords ? coords : undefined,
    });
    setAskText('');
  };

  const handleRun = () => {
    if (!prompt.trim() || !selectedModule) return;
    const site = (lat && lng) ? { lat: parseFloat(lat), lng: parseFloat(lng) } : undefined;
    startReasoning({
      module: selectedModule,
      prompt,
      run_mode: runMode,
      allow_web_fetch: allowWebFetch,
      site_data: site,
    });
  };

  const handleExampleClick = (example: string) => {
    setPrompt(example);
  };

  const currentModule = selectedModule ? MODULES.find(m => m.id === selectedModule)! : null;

  // (Auto-run handled inline in handleAsk to avoid extra state)

  return (
    <div className="min-h-screen bg-white">
      <AnimatePresence mode="wait">
        {!selectedModule ? (
          <motion.div
            key="module-selector"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-white"
          >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-slate-900">Welcome to The Planner's Assistant</h1>
                <p className="text-sm text-slate-600 mt-2">Your comprehensive toolkit for modern urban and regional planning. Select a tool below to get started.</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {MODULES.map((module) => (
                  <button
                    key={module.id}
                    onClick={() => handleModuleSelect(module.id)}
                    className="p-4 rounded-xl border-2 border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50 hover:shadow-md transition-all text-left"
                  >
                    <div className="text-2xl mb-2">{module.icon}</div>
                    <div className="text-sm font-semibold mb-1 text-slate-900">{module.label}</div>
                    <div className="text-xs text-slate-500">{module.description}</div>
                  </button>
                ))}
              </div>
              <div className="mt-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-px flex-1 bg-slate-200" />
                  <span className="text-xs font-medium text-slate-500">or</span>
                  <div className="h-px flex-1 bg-slate-200" />
                </div>
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-4">
                  <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
                    <label className="sr-only" htmlFor="ask-text">Ask a question</label>
                    <input
                      id="ask-text"
                      type="text"
                      value={askText}
                      onChange={(e) => setAskText(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleAsk(); }}
                      placeholder="Or ask a question… (we'll pick the best tool)"
                      className="flex-1 px-4 py-2 rounded-lg border-2 border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500"
                      disabled={isRunning}
                    />
                    <button
                      onClick={handleAsk}
                      disabled={isRunning || !askText.trim()}
                      className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[color:var(--ink)] text-[color:var(--brand)] text-sm font-semibold shadow hover:brightness-110 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Sparkles className="w-4 h-4" /> Ask
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">We'll auto-pick the right tool, move your question into the prompt, and start streaming.</p>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="tool-interface"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex items-center gap-4">
                  <button onClick={handleBack} className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Tools
                  </button>
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-2xl">{currentModule!.icon}</span>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">{currentModule!.label}</h2>
                      <p className="text-xs text-slate-600">{currentModule!.description}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 space-y-4">
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                    <div className="flex items-center justify-between mb-3">
                      <label className="block text-sm font-semibold text-slate-900">📝 Describe your planning query</label>
                      <button type="button" onClick={() => setShowSettings((v) => !v)} className="text-xs text-slate-600 hover:text-teal-700 px-2 py-1 rounded-lg hover:bg-slate-100">
                        <Settings className="w-3.5 h-3.5 inline mr-1" /> Settings
                      </button>
                    </div>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder={currentModule ? `E.g., "${EXAMPLE_PROMPTS[selectedModule][0]}"` : ''}
                      rows={5}
                      className="w-full px-4 py-3 rounded-lg border-2 border-slate-200 focus:border-teal-500 focus:outline-none resize-none text-slate-900 placeholder-slate-400"
                      disabled={isRunning}
                    />
                    <div className="mt-3 space-y-2">
                      <div className="text-xs font-medium text-slate-600 mb-2">💡 Try an example:</div>
                      {currentModule && EXAMPLE_PROMPTS[selectedModule].slice(0, 2).map((example, i) => (
                        <button key={i} onClick={() => handleExampleClick(example)} disabled={isRunning} className="w-full text-left px-3 py-2 text-xs rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50">
                          {example}
                        </button>
                      ))}
                    </div>
                    {(selectedModule === 'evidence' || selectedModule === 'dm') && (
                      <div className="mt-4 pt-4 border-t border-slate-200">
                        <button onClick={() => setShowSiteInput(!showSiteInput)} className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-teal-600 transition-colors">
                          <MapPin className="w-4 h-4" />
                          {showSiteInput ? 'Hide' : 'Add'} Site Coordinates
                        </button>
                        <AnimatePresence>
                          {showSiteInput && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-3 grid grid-cols-2 gap-2">
                              <input type="number" step="any" placeholder="Latitude" value={lat} onChange={(e) => setLat(e.target.value)} className="px-3 py-2 rounded-lg border-2 border-slate-200 focus:border-teal-500 focus:outline-none text-sm" disabled={isRunning} />
                              <input type="number" step="any" placeholder="Longitude" value={lng} onChange={(e) => setLng(e.target.value)} className="px-3 py-2 rounded-lg border-2 border-slate-200 focus:border-teal-500 focus:outline-none text-sm" disabled={isRunning} />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}
                    <button onClick={handleRun} disabled={isRunning || !prompt.trim()} className="w-full mt-4 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                      {isRunning ? (
                        <>
                          <Sparkles className="w-5 h-5 animate-pulse" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Play className="w-5 h-5" />
                          Run Analysis
                        </>
                      )}
                    </button>
                  </div>
                  <AnimatePresence>
                    {showSettings && (
                      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm font-semibold text-slate-900">⚙️ Settings</h3>
                          <button onClick={() => setShowSettings(false)} className="p-1 hover:bg-slate-100 rounded"><X className="w-4 h-4" /></button>
                        </div>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-xs font-medium text-slate-700 mb-2">Analysis Mode</label>
                            <div className="grid grid-cols-2 gap-2">
                              <button onClick={() => setRunMode('stable')} disabled={isRunning} className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${runMode === 'stable' ? 'bg-teal-500 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                                <Zap className="w-3 h-3 inline mr-1" />Fast
                              </button>
                              <button onClick={() => setRunMode('deep')} disabled={isRunning} className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${runMode === 'deep' ? 'bg-teal-500 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                                <Shield className="w-3 h-3 inline mr-1" />Deep
                              </button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between">
                            <label className="text-xs font-medium text-slate-700">Allow Web Fetch</label>
                            <button onClick={() => setAllowWebFetch(!allowWebFetch)} disabled={isRunning} className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${allowWebFetch ? 'bg-teal-500' : 'bg-slate-300'}`}>
                              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${allowWebFetch ? 'translate-x-6' : 'translate-x-1'}`} />
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  {reasoning && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-4 h-4 text-teal-600" />
                        <h3 className="text-sm font-semibold text-slate-900">AI Reasoning</h3>
                      </div>
                      <div className="prose prose-sm prose-slate max-w-none text-slate-600 leading-relaxed max-h-64 overflow-y-auto">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ node, inline, className, children, ...props }: any) {
                              const match = /language-(\w+)/.exec(className || '');
                              return !inline && match ? (
                                <SyntaxHighlighter
                                  style={vscDarkPlus}
                                  language={match[1]}
                                  PreTag="div"
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {reasoning}
                        </ReactMarkdown>
                      </div>
                    </motion.div>
                  )}
                </div>
                <div className="lg:col-span-2">
                  <ErrorBoundary>
                    <PanelHost panels={panels} module={selectedModule} />
                  </ErrorBoundary>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
