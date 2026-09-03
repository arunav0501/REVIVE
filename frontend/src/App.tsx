import { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  AlertCircle, 
  RefreshCw, 
  Workflow, 
  Search, 
  Filter, 
  ArrowUpDown, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  FileText, 
  Building2, 
  AlertTriangle, 
  BrainCircuit, 
  Sparkles, 
  Flame, 
  HelpCircle, 
  TrendingUp, 
  DollarSign, 
  Clock, 
  PieChart as PieChartIcon, 
  BarChart3, 
  ShieldAlert, 
  ArrowUpRight, 
  Send, 
  History, 
  CheckCircle2, 
  Phone, 
  Globe, 
  Mail, 
  FileCode2, 
  Calendar, 
  Layers, 
  BookOpen, 
  FileCheck, 
  Bot, 
  Play, 
  Copy, 
  Check, 
  Cpu, 
  CheckCircle,
  Repeat,
  Zap,
  CheckCheck
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';
import { 
  fetchHealth, 
  fetchClaims, 
  fetchClaimDetail, 
  fetchPriorityClaims, 
  fetchModelMetrics, 
  predictClaim, 
  fetchDashboardMetrics, 
  fetchAgingBuckets, 
  fetchPayerPerformance, 
  fetchDenialReasons, 
  fetchPriorityDistribution, 
  searchPolicyKnowledge, 
  fetchClaimPolicyContext, 
  fetchAgentDecision, 
  executeAgentAction, 
  fetchAgentActions, 
  generateArtifacts, 
  simulatePayerResponse, 
  fetchOutcomeProbabilities,
  runClosedLoopRecovery
} from './services/api';
import type { 
  HealthStatus, 
  PaginatedClaims, 
  ClaimItem, 
  ClaimDetail, 
  MLMetricsResponse, 
  DashboardMetrics, 
  AgingBucket, 
  PayerPerformance, 
  DenialReasonItem, 
  PriorityDistributionItem, 
  PolicyChunk, 
  AgentDecision, 
  AgentActionItem, 
  GeneratedArtifacts, 
  SimulationResultResponse, 
  OutcomeProbabilityDistribution,
  ClosedLoopRunResponse
} from './types';

const PRIORITY_COLORS: Record<string, string> = {
  Critical: '#ef4444',
  High: '#f59e0b',
  Medium: '#3b82f6',
  Low: '#64748b',
};

const DENIAL_COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#ec4899', '#f97316', '#10b981', '#6366f1'];

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<MLMetricsResponse | null>(null);
  const [dashMetrics, setDashMetrics] = useState<DashboardMetrics | null>(null);
  const [agingData, setAgingData] = useState<AgingBucket[]>([]);
  const [payerPerf, setPayerPerf] = useState<PayerPerformance[]>([]);
  const [denialReasons, setDenialReasons] = useState<DenialReasonItem[]>([]);
  const [priorityDist, setPriorityDist] = useState<PriorityDistributionItem[]>([]);

  // Navigation tab state
  const [activeTab, setActiveTab] = useState<'dashboard' | 'all' | 'priority' | 'closedloop' | 'simulator' | 'generator' | 'agent' | 'rag' | 'ml' | 'system'>('dashboard');
  
  // Claims state
  const [claimsData, setClaimsData] = useState<PaginatedClaims | null>(null);
  const [priorityClaims, setPriorityClaims] = useState<ClaimItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & pagination
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [search, setSearch] = useState<string>('');
  const [payerFilter, setPayerFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [bandFilter, setBandFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('priority_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Selected claim detail modal state & tabs
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [claimDetail, setClaimDetail] = useState<ClaimDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [modalTab, setModalTab] = useState<'strategy' | 'clinical' | 'payer' | 'timeline'>('strategy');
  const [claimRagChunks, setClaimRagChunks] = useState<PolicyChunk[]>([]);

  // RAG Search State
  const [ragQuery, setRagQuery] = useState<string>('missing documentation appeal required documents');
  const [ragPayerFilter, setRagPayerFilter] = useState<string>('');
  const [ragResults, setRagResults] = useState<PolicyChunk[]>([]);
  const [loadingRag, setLoadingRag] = useState<boolean>(false);

  // AI Agent State
  const [agentClaimId, setAgentClaimId] = useState<string>('CLM0003394');
  const [agentDecision, setAgentDecision] = useState<AgentDecision | null>(null);
  const [loadingAgentDecision, setLoadingAgentDecision] = useState<boolean>(false);
  const [executingAgent, setExecutingAgent] = useState<boolean>(false);
  const [agentExecutionSuccess, setAgentExecutionSuccess] = useState<string | null>(null);
  const [agentActionHistory, setAgentActionHistory] = useState<AgentActionItem[]>([]);

  // Phase 10 Follow-Up Generator State
  const [genClaimId, setGenClaimId] = useState<string>('CLM0003394');
  const [genFormat, setGenFormat] = useState<'appeal_letter' | 'portal_message' | 'phone_script' | 'email_template' | 'edi_resubmission_note'>('appeal_letter');
  const [genTone, setGenTone] = useState<'firm' | 'urgent' | 'collaborative'>('urgent');
  const [genCustomNotes, setGenCustomNotes] = useState<string>('Enclosing certified operative report and itemized billing statements for immediate reconsideration.');
  const [generatedArtifacts, setGeneratedArtifacts] = useState<GeneratedArtifacts | null>(null);
  const [loadingGenerator, setLoadingGenerator] = useState<boolean>(false);
  const [copiedMessage, setCopiedMessage] = useState<boolean>(false);

  // Phase 11 Payer Simulator State
  const [simClaimId, setSimClaimId] = useState<string>('CLM0003394');
  const [simActionType, setSimActionType] = useState<string>('Appeal');
  const [simChannel, setSimChannel] = useState<string>('Portal');
  const [simQuality, setSimQuality] = useState<string>('high');
  const [simProbabilities, setSimProbabilities] = useState<OutcomeProbabilityDistribution | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResultResponse | null>(null);
  const [loadingSimulation, setLoadingSimulation] = useState<boolean>(false);

  // Phase 12 Closed Loop Engine State
  const [loopBatchSize, setLoopBatchSize] = useState<number>(10);
  const [loopMinBand, setLoopMinBand] = useState<string>('High');
  const [loopPayer, setLoopPayer] = useState<string>('');
  const [loopQuality, setLoopQuality] = useState<string>('high');
  const [loopResponse, setLoopResponse] = useState<ClosedLoopRunResponse | null>(null);
  const [runningLoop, setRunningLoop] = useState<boolean>(false);

  const loadDashboardData = async () => {
    try {
      const [h, m, dm, aging, payers, denials, dist] = await Promise.all([
        fetchHealth(),
        fetchModelMetrics(),
        fetchDashboardMetrics(),
        fetchAgingBuckets(),
        fetchPayerPerformance(),
        fetchDenialReasons(),
        fetchPriorityDistribution(),
      ]);
      setHealth(h);
      setMetrics(m);
      setDashMetrics(dm);
      setAgingData(aging);
      setPayerPerf(payers);
      setDenialReasons(denials);
      setPriorityDist(dist);
    } catch (err: any) {
      console.error('Error loading dashboard analytics:', err);
      setError(err?.message || 'Failed to load dashboard data');
    }
  };

  const handleRagSearch = useCallback(async () => {
    if (!ragQuery.trim()) return;
    setLoadingRag(true);
    try {
      const resp = await searchPolicyKnowledge(ragQuery.trim(), ragPayerFilter || undefined, 6);
      setRagResults(resp.chunks);
    } catch (err: any) {
      console.error('Error performing RAG search:', err);
    } finally {
      setLoadingRag(false);
    }
  }, [ragQuery, ragPayerFilter]);

  const loadAgentActions = async () => {
    try {
      const history = await fetchAgentActions(15);
      setAgentActionHistory(history);
    } catch (err: any) {
      console.error('Error loading agent actions:', err);
    }
  };

  const handleFormulateDecision = async (claimId: string) => {
    setLoadingAgentDecision(true);
    setAgentExecutionSuccess(null);
    try {
      const decision = await fetchAgentDecision(claimId);
      setAgentDecision(decision);
    } catch (err: any) {
      console.error('Error formulating agent decision:', err);
      setError(err?.message || 'Failed to formulate agent decision');
    } finally {
      setLoadingAgentDecision(false);
    }
  };

  const handleGenerateArtifacts = useCallback(async () => {
    if (!genClaimId.trim()) return;
    setLoadingGenerator(true);
    try {
      const art = await generateArtifacts(genClaimId.trim(), 'all', genTone, genCustomNotes.trim() || undefined);
      setGeneratedArtifacts(art);
    } catch (err: any) {
      console.error('Error generating follow-up artifacts:', err);
      setError(err?.message || 'Failed to generate follow-up artifacts');
    } finally {
      setLoadingGenerator(false);
    }
  }, [genClaimId, genTone, genCustomNotes]);

  const handleFetchSimProbabilities = useCallback(async () => {
    if (!simClaimId.trim()) return;
    try {
      const probs = await fetchOutcomeProbabilities(simClaimId.trim(), simActionType, simQuality);
      setSimProbabilities(probs);
    } catch (err: any) {
      console.error('Error fetching simulation probabilities:', err);
    }
  }, [simClaimId, simActionType, simQuality]);

  const handleSimulateResponse = async (applyToDb: boolean = false) => {
    if (!simClaimId.trim()) return;
    setLoadingSimulation(true);
    try {
      const res = await simulatePayerResponse(simClaimId.trim(), simActionType, simChannel, simQuality, applyToDb);
      setSimulationResult(res);
      setSimProbabilities(res.probability_distribution);
      if (applyToDb) {
        await loadDashboardData();
        if (selectedClaimId === simClaimId.trim()) {
          const updated = await fetchClaimDetail(simClaimId.trim());
          setClaimDetail(updated);
        }
      }
    } catch (err: any) {
      console.error('Error simulating payer response:', err);
      setError(err?.message || 'Failed to simulate payer response');
    } finally {
      setLoadingSimulation(false);
    }
  };

  const handleRunClosedLoop = async () => {
    setRunningLoop(true);
    setError(null);
    try {
      const resp = await runClosedLoopRecovery(loopBatchSize, loopMinBand, loopPayer || undefined, loopQuality);
      setLoopResponse(resp);
      await loadDashboardData();
    } catch (err: any) {
      console.error('Error executing closed loop recovery:', err);
      setError(err?.message || 'Failed to execute closed loop recovery');
    } finally {
      setRunningLoop(false);
    }
  };

  const handleExecuteAction = async (simulate: boolean = true) => {
    if (!agentDecision) return;
    setExecutingAgent(true);
    setAgentExecutionSuccess(null);
    try {
      const res = await executeAgentAction(agentDecision.claim_id, simulate);
      setAgentExecutionSuccess(`Action successfully ${simulate ? 'simulated' : 'executed'} (Action ID: #${res.action_id})`);
      await loadAgentActions();
      if (selectedClaimId === agentDecision.claim_id) {
        const updated = await fetchClaimDetail(agentDecision.claim_id);
        setClaimDetail(updated);
      }
    } catch (err: any) {
      console.error('Error executing agent action:', err);
      setError(err?.message || 'Failed to execute agent action');
    } finally {
      setExecutingAgent(false);
    }
  };

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchClaims({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        payer_id: payerFilter || undefined,
        claim_status: statusFilter || undefined,
        priority_band: bandFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setClaimsData(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load claims from backend');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, payerFilter, statusFilter, bandFilter, sortBy, sortOrder]);

  const loadPriority = async () => {
    setLoading(true);
    try {
      const items = await fetchPriorityClaims(20, undefined, bandFilter || undefined);
      setPriorityClaims(items);
    } catch (err: any) {
      setError(err?.message || 'Failed to load priority claims');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    handleRagSearch();
    loadAgentActions();
    handleFormulateDecision('CLM0003394');
    handleGenerateArtifacts();
    handleFetchSimProbabilities();
  }, [handleRagSearch, handleGenerateArtifacts, handleFetchSimProbabilities]);

  useEffect(() => {
    if (activeTab === 'all') {
      loadClaims();
    } else if (activeTab === 'priority') {
      loadPriority();
    } else if (activeTab === 'dashboard') {
      loadDashboardData();
    } else if (activeTab === 'agent') {
      loadAgentActions();
    } else if (activeTab === 'generator') {
      handleGenerateArtifacts();
    } else if (activeTab === 'simulator') {
      handleFetchSimProbabilities();
    }
  }, [activeTab, loadClaims, handleGenerateArtifacts, handleFetchSimProbabilities]);

  const handleOpenDetail = async (claimId: string) => {
    setSelectedClaimId(claimId);
    setLoadingDetail(true);
    setModalTab('strategy');
    setClaimRagChunks([]);
    try {
      const [detail, chunks] = await Promise.all([
        fetchClaimDetail(claimId),
        fetchClaimPolicyContext(claimId),
      ]);
      setClaimDetail(detail);
      setClaimRagChunks(chunks);
      await predictClaim(claimId);
    } catch (err: any) {
      console.error('Error fetching claim details or RAG context:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedClaimId(null);
    setClaimDetail(null);
    setClaimRagChunks([]);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Paid':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'Denied':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'Appeal Pending':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'Pending':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const getPriorityBandBadge = (band?: string | null) => {
    switch (band) {
      case 'Critical':
        return 'bg-red-500/20 text-red-300 border-red-500/40 ring-1 ring-red-500/30 font-bold';
      case 'High':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30 font-semibold';
      case 'Medium':
        return 'bg-blue-500/15 text-blue-300 border-blue-500/30 font-medium';
      case 'Low':
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700 font-normal';
    }
  };

  const getChannelIcon = (channel?: string | null) => {
    const ch = (channel || '').toLowerCase();
    if (ch.includes('portal') || ch.includes('web')) return <Globe className="w-4 h-4 text-blue-400" />;
    if (ch.includes('phone') || ch.includes('call')) return <Phone className="w-4 h-4 text-emerald-400" />;
    if (ch.includes('mail')) return <Mail className="w-4 h-4 text-amber-400" />;
    return <FileCode2 className="w-4 h-4 text-purple-400" />;
  };

  const getOutcomeStyle = (outcome: string) => {
    switch (outcome) {
      case 'APPROVED_FULL':
        return { label: 'Approved In Full (100%)', badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' };
      case 'APPROVED_PARTIAL':
        return { label: 'Partial Payment Approved', badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' };
      case 'ADDITIONAL_INFO_REQUIRED':
        return { label: 'Additional Docs Required', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
      case 'DENIAL_UPHELD':
      default:
        return { label: 'Denial Upheld / Rejected', badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40' };
    }
  };

  const getCurrentArtifactContent = (): string => {
    if (!generatedArtifacts) return 'No artifact generated yet.';
    switch (genFormat) {
      case 'appeal_letter':
        return generatedArtifacts.appeal_letter || 'No appeal letter generated.';
      case 'portal_message':
        return generatedArtifacts.portal_message || 'No portal message generated.';
      case 'phone_script':
        return generatedArtifacts.phone_script || 'No phone script generated.';
      case 'email_template':
        return generatedArtifacts.email_template || 'No email template generated.';
      case 'edi_resubmission_note':
        return generatedArtifacts.edi_resubmission_note || 'No EDI note generated.';
      default:
        return generatedArtifacts.appeal_letter || '';
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-[#0d131f]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-blue-400/30">
              <Workflow className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  RecoverAI
                </span>
                <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  AR Follow-Up AI
                </span>
              </div>
              <p className="text-xs text-slate-400">Autonomous Healthcare Revenue Recovery System</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-300 font-medium">Phase 12 Closed-Loop Live</span>
            </div>

            <button
              onClick={() => {
                loadDashboardData();
                if (activeTab === 'all') loadClaims();
                else if (activeTab === 'priority') loadPriority();
                else if (activeTab === 'rag') handleRagSearch();
                else if (activeTab === 'agent') loadAgentActions();
                else if (activeTab === 'generator') handleGenerateArtifacts();
                else if (activeTab === 'simulator') handleFetchSimProbabilities();
              }}
              disabled={loading || loadingRag || loadingAgentDecision || loadingGenerator || loadingSimulation || runningLoop}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:opacity-50 text-xs font-semibold text-white shadow-sm transition-all cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${(loading || loadingRag || loadingAgentDecision || loadingGenerator || loadingSimulation || runningLoop) ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Executive Dashboard</span>
            </button>
            <button
              onClick={() => setActiveTab('closedloop')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'closedloop'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20 ring-1 ring-blue-400/50'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Repeat className="w-3.5 h-3.5 text-cyan-400" />
              <span>Closed Loop Engine</span>
            </button>
            <button
              onClick={() => { setActiveTab('all'); setPage(1); }}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'all'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Claims Explorer ({claimsData?.total ? claimsData.total.toLocaleString() : '10,000'})
            </button>
            <button
              onClick={() => setActiveTab('priority')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'priority'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              <span>Priority Queue (Top 20)</span>
            </button>
            <button
              onClick={() => setActiveTab('simulator')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'simulator'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>Payer Simulator</span>
            </button>
            <button
              onClick={() => setActiveTab('generator')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'generator'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <FileCode2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Follow-Up Studio</span>
            </button>
            <button
              onClick={() => setActiveTab('agent')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'agent'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Bot className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Follow-Up Agent</span>
            </button>
            <button
              onClick={() => setActiveTab('rag')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'rag'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
              <span>Payer Policy RAG</span>
            </button>
            <button
              onClick={() => setActiveTab('ml')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'ml'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>ML Model Metrics</span>
            </button>
            <button
              onClick={() => setActiveTab('system')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'system'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Diagnostics
            </button>
          </div>

          <div className="text-xs text-slate-400 font-mono hidden md:block">
            Engine: <span className="text-cyan-400">Autonomous Closed Loop Active</span>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="rounded-xl bg-red-950/40 border border-red-500/30 p-4 flex items-start space-x-3 text-red-200 text-sm shadow-lg">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Error</p>
              <p className="text-xs text-red-400/90 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* TAB: CLOSED LOOP RECOVERY ENGINE (PHASE 12) */}
        {activeTab === 'closedloop' && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-br from-[#0e1d2e] via-[#0b1624] to-[#070e17] border border-cyan-500/40 p-6 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-2">
                    <Repeat className="w-3.5 h-3.5" />
                    <span>Phase 12 — Closed-Loop Autonomous Recovery Engine</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">Autonomous Revenue Cycle Loop</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    Executes the full 7-step cycle: Ingestion → Agent Decision → Artifact Generation → Payer Adjudication → Ledger Update → Recovery Recording → Analytics Recomputation.
                  </p>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleRunClosedLoop}
                    disabled={runningLoop}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-extrabold text-xs shadow-lg shadow-cyan-500/20 transition-all cursor-pointer flex items-center space-x-2 disabled:opacity-50"
                  >
                    <Zap className={`w-4 h-4 ${runningLoop ? 'animate-spin' : ''}`} />
                    <span>{runningLoop ? 'Executing Loop...' : `Run Loop (${loopBatchSize} Claims)`}</span>
                  </button>
                </div>
              </div>

              {/* Loop Configuration Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-950/80 border border-slate-800">
                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Batch Size</span>
                  <div className="flex space-x-1.5">
                    {[10, 20, 30, 50].map((sz) => (
                      <button
                        key={sz}
                        onClick={() => setLoopBatchSize(sz)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                          loopBatchSize === sz
                            ? 'bg-cyan-600 text-white'
                            : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                      >
                        {sz}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Min Priority Band</span>
                  <select
                    value={loopMinBand}
                    onChange={(e) => setLoopMinBand(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="High">🔥 High & Critical (Recommended)</option>
                    <option value="Critical">⚡ Critical Only</option>
                    <option value="Medium">✦ Medium & Above</option>
                    <option value="All">All Prioritized Claims</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Target Payer</span>
                  <select
                    value={loopPayer}
                    onChange={(e) => setLoopPayer(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">All Payers (10 Payers)</option>
                    <option value="PAY001">PAY001 - BlueCross Health</option>
                    <option value="PAY002">PAY002 - AetnaCare</option>
                    <option value="PAY003">PAY003 - UnitedCare</option>
                    <option value="PAY004">PAY004 - Cigna Health</option>
                    <option value="PAY005">PAY005 - Medicare Adv</option>
                    <option value="PAY006">PAY006 - Medicaid</option>
                    <option value="PAY007">PAY007 - Humana Plus</option>
                    <option value="PAY008">PAY008 - Kaiser Health</option>
                    <option value="PAY009">PAY009 - Anthem Blue</option>
                    <option value="PAY010">PAY010 - Molina Health</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Action Quality</span>
                  <select
                    value={loopQuality}
                    onChange={(e) => setLoopQuality(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="high">🌟 High (Grounded RAG + Certified Exhibits)</option>
                    <option value="standard">⚖️ Standard Form Filing</option>
                  </select>
                </div>
              </div>

              {/* Loop Run Results Summary */}
              {loopResponse && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase">Claims Processed</span>
                      <div className="text-2xl font-mono font-extrabold text-white mt-1">
                        {loopResponse.total_processed}
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1 font-mono">Run ID: {loopResponse.run_id}</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 flex flex-col justify-between">
                      <span className="text-[11px] font-semibold text-emerald-400 uppercase">Recovered Dollars</span>
                      <div className="text-2xl font-mono font-extrabold text-emerald-300 mt-1">
                        ${loopResponse.total_recovered.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                      <span className="text-[10px] text-emerald-400 mt-1">Committed to SQLite DB</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-cyan-950/40 border border-cyan-500/40 flex flex-col justify-between">
                      <span className="text-[11px] font-semibold text-cyan-400 uppercase">Recovery Yield</span>
                      <div className="text-2xl font-mono font-extrabold text-cyan-300 mt-1">
                        {loopResponse.recovery_yield_percentage}%
                      </div>
                      <span className="text-[10px] text-slate-400 mt-1 font-mono">of ${loopResponse.total_original_outstanding.toLocaleString()} outstanding</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
                      <span className="text-[11px] font-semibold text-purple-400 uppercase">Outcome Breakdown</span>
                      <div className="text-xs font-mono space-y-0.5 mt-1 text-slate-300">
                        <div>Full Approval: <strong className="text-emerald-400">{loopResponse.outcomes_breakdown.APPROVED_FULL || 0}</strong></div>
                        <div>Partial Payment: <strong className="text-cyan-400">{loopResponse.outcomes_breakdown.APPROVED_PARTIAL || 0}</strong></div>
                        <div>Need Info / Denied: <strong className="text-amber-400">{(loopResponse.outcomes_breakdown.ADDITIONAL_INFO_REQUIRED || 0) + (loopResponse.outcomes_breakdown.DENIAL_UPHELD || 0)}</strong></div>
                      </div>
                    </div>
                  </div>

                  {/* Granular Claim Results Table */}
                  <div className="rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden shadow-xl">
                    <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                        <CheckCheck className="w-4 h-4 text-emerald-400" />
                        <span>Execution Ledger for {loopResponse.results.length} Claims</span>
                      </h4>
                      <span className="text-xs font-mono text-slate-400">All State Transitions Recorded</span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[#070b12] text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-800">
                          <tr>
                            <th className="py-3 px-4">Claim ID</th>
                            <th className="py-3 px-4">Payer</th>
                            <th className="py-3 px-4">Initial Status</th>
                            <th className="py-3 px-4">Action Chosen</th>
                            <th className="py-3 px-4">Adjudication Outcome</th>
                            <th className="py-3 px-4 text-right">Recovered ($)</th>
                            <th className="py-3 px-4 text-right">Final Outstanding</th>
                            <th className="py-3 px-4 text-center">Final Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-mono">
                          {loopResponse.results.map((r) => (
                            <tr key={r.claim_id} className="hover:bg-slate-900/50 transition-colors">
                              <td className="py-3 px-4 font-bold text-blue-400">{r.claim_id}</td>
                              <td className="py-3 px-4 font-sans text-slate-300">{r.payer_name}</td>
                              <td className="py-3 px-4 font-sans text-slate-400">{r.initial_status}</td>
                              <td className="py-3 px-4 font-sans">
                                <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px] font-semibold">
                                  {r.chosen_action}
                                </span>
                              </td>
                              <td className="py-3 px-4 font-sans">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getOutcomeStyle(r.simulated_outcome).badge}`}>
                                  {getOutcomeStyle(r.simulated_outcome).label}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right font-bold text-emerald-400">
                                ${r.recovered_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </td>
                              <td className="py-3 px-4 text-right text-slate-300">
                                ${r.final_outstanding.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </td>
                              <td className="py-3 px-4 text-center font-sans">
                                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(r.final_status)}`}>
                                  {r.final_status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 0: EXECUTIVE DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-slate-800/80 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total AR</span>
                  <div className="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <DollarSign className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-white">
                    ${dashMetrics ? (dashMetrics.total_ar / 1000000).toFixed(2) + 'M' : '—'}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">10,000 Total Claims</p>
                </div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-emerald-500/30 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Expected Recovery</span>
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-emerald-400">
                    ${dashMetrics ? (dashMetrics.expected_recovery / 1000000).toFixed(2) + 'M' : '—'}
                  </div>
                  <p className="text-[11px] text-emerald-300/80 mt-0.5">
                    {dashMetrics ? ((dashMetrics.expected_recovery / dashMetrics.total_ar) * 100).toFixed(1) : '63.6'}% Recovery Yield
                  </p>
                </div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-red-500/30 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">High Risk Claims</span>
                  <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                    <Flame className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-rose-300">
                    {dashMetrics ? (dashMetrics.critical_claims + dashMetrics.high_priority_claims).toLocaleString() : '—'}
                  </div>
                  <p className="text-[11px] text-rose-400/80 mt-0.5">Critical & High Priority</p>
                </div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-slate-800/80 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recovered Rev</span>
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-cyan-300">
                    ${dashMetrics ? (dashMetrics.recovered_revenue / 1000000).toFixed(2) + 'M' : '—'}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Outcomes Resolved</p>
                </div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-slate-800/80 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Avg Days in AR</span>
                  <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                    <Clock className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-amber-300">
                    {dashMetrics ? `${dashMetrics.avg_days_in_ar}d` : '—'}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Aging Portfolio Mean</p>
                </div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-[#0e1626] to-[#090d16] border border-slate-800/80 p-5 shadow-lg flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider">Denial Rate</span>
                  <div className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xl font-extrabold font-mono text-purple-300">
                    {dashMetrics ? `${dashMetrics.denial_rate}%` : '—'}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">2,597 Denied Claims</p>
                </div>
              </div>
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 rounded-2xl bg-slate-900/60 border border-slate-800 p-6 shadow-xl flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-blue-400" />
                      <span>AR Aging Breakdown vs. ML Expected Recovery</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Standard healthcare aging intervals across $44.05M total AR</p>
                  </div>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={agingData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#64748b" tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`} tick={{ fontSize: 11 }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                        formatter={(value: any) => [`$${Number(value).toLocaleString()}`, '']}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Bar dataKey="total_outstanding" name="Total Outstanding ($)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="expected_recovery" name="Expected Recovery ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 shadow-xl flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <PieChartIcon className="w-4 h-4 text-purple-400" />
                      <span>Priority Distribution</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">10,000 claims mapped into priority bands</p>
                  </div>
                </div>

                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={priorityDist}
                        dataKey="count"
                        nameKey="band"
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={75}
                        paddingAngle={4}
                      >
                        {priorityDist.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PRIORITY_COLORS[entry.band] || '#64748b'} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                        formatter={(value: any, name: any) => [`${Number(value).toLocaleString()} claims`, name]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                  {priorityDist.map((item) => (
                    <div 
                      key={item.band} 
                      onClick={() => { setBandFilter(item.band); setActiveTab('all'); setPage(1); }}
                      className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 hover:border-blue-500/50 transition-all cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PRIORITY_COLORS[item.band] }}></span>
                          <span className="font-semibold text-slate-200">{item.band}</span>
                        </div>
                        <span className="font-mono text-slate-400 text-[10px]">{item.percentage}%</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        ${(item.total_outstanding / 1000000).toFixed(2)}M • {item.count.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Charts Row 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 shadow-xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <Building2 className="w-4 h-4 text-cyan-400" />
                      <span>Payer Financial Exposure & Recovery</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Ranked by total outstanding AR volume across 10 payers</p>
                  </div>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={payerPerf} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="payer_name" stroke="#64748b" tick={{ fontSize: 9 }} angle={-25} textAnchor="end" />
                      <YAxis stroke="#64748b" tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`} tick={{ fontSize: 11 }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                        formatter={(value: any) => [`$${Number(value).toLocaleString()}`, '']}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Bar dataKey="total_outstanding" name="Outstanding AR ($)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="expected_recovery" name="Expected Recovery ($)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 shadow-xl flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                      <span>Top Denial Reasons Exposure</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Breakdown of 2,597 denied claims by root cause</p>
                  </div>
                </div>

                <div className="space-y-3">
                  {denialReasons.map((item, idx) => (
                    <div key={item.reason} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-200 font-medium truncate max-w-[240px]">{item.reason}</span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          ${(item.total_outstanding / 1000000).toFixed(2)}M ({item.count} claims)
                        </span>
                      </div>
                      <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{ 
                            width: `${item.percentage}%`, 
                            backgroundColor: DENIAL_COLORS[idx % DENIAL_COLORS.length] 
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Root causes derived from 835 Remittance records</span>
                  <button
                    onClick={() => { setStatusFilter('Denied'); setActiveTab('all'); setPage(1); }}
                    className="text-blue-400 hover:text-blue-300 font-semibold flex items-center space-x-1 cursor-pointer"
                  >
                    <span>View all denied claims</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 1: ALL CLAIMS EXPLORER */}
        {activeTab === 'all' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-4 shadow-lg space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                <div className="relative md:col-span-2">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    placeholder="Search Claim ID, Patient ID, Provider, Denial reason..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                    className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>

                <div className="relative">
                  <Flame className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <select
                    value={bandFilter}
                    onChange={(e) => { setBandFilter(e.target.value); setPage(1); }}
                    className="w-full pl-9 pr-8 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500 appearance-none transition-colors"
                  >
                    <option value="">All Priority Bands</option>
                    <option value="Critical">🔥 Critical (85-100)</option>
                    <option value="High">⚡ High (70-85)</option>
                    <option value="Medium">✦ Medium (40-70)</option>
                    <option value="Low">Low (0-40)</option>
                  </select>
                </div>

                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <select
                    value={payerFilter}
                    onChange={(e) => { setPayerFilter(e.target.value); setPage(1); }}
                    className="w-full pl-9 pr-8 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500 appearance-none transition-colors"
                  >
                    <option value="">All Payers (10 Payers)</option>
                    <option value="PAY001">PAY001 - BlueCross Health</option>
                    <option value="PAY002">PAY002 - AetnaCare</option>
                    <option value="PAY003">PAY003 - UnitedCare</option>
                    <option value="PAY004">PAY004 - Cigna Health</option>
                    <option value="PAY005">PAY005 - Humana Plus</option>
                    <option value="PAY006">PAY006 - Molina Health</option>
                    <option value="PAY007">PAY007 - Anthem Blue</option>
                    <option value="PAY008">PAY008 - Kaiser Health</option>
                    <option value="PAY009">PAY009 - Centene Care</option>
                    <option value="PAY010">PAY010 - Medicare Adv</option>
                  </select>
                </div>

                <div className="relative">
                  <Filter className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                    className="w-full pl-9 pr-8 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500 appearance-none transition-colors"
                  >
                    <option value="">All Claim Statuses</option>
                    <option value="Pending">Pending</option>
                    <option value="Appeal Pending">Appeal Pending</option>
                    <option value="Denied">Denied</option>
                    <option value="Paid">Paid</option>
                    <option value="In Review">In Review</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                <div className="flex items-center space-x-2">
                  <span className="text-[11px] font-medium">Sort by:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
                  >
                    <option value="priority_score">Priority Score (ML Prioritized)</option>
                    <option value="outstanding_amount">Outstanding Amount ($)</option>
                    <option value="days_in_ar">Days in AR (Aging)</option>
                    <option value="billed_amount">Billed Amount ($)</option>
                    <option value="claim_date">Claim Date</option>
                    <option value="followup_count">Follow-Up Count</option>
                  </select>

                  <button
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-colors cursor-pointer"
                  >
                    <ArrowUpDown className="w-3 h-3 text-blue-400" />
                    <span>{sortOrder === 'desc' ? 'Descending' : 'Ascending'}</span>
                  </button>
                </div>

                <div className="text-[11px] text-slate-400">
                  Showing <span className="text-white font-semibold">{claimsData?.items.length || 0}</span> of <span className="text-white font-semibold">{claimsData?.total.toLocaleString() || 0}</span> total matching claims
                </div>
              </div>
            </div>

            {/* Claims Table */}
            <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3.5 px-4">Priority</th>
                      <th className="py-3.5 px-4">Claim ID</th>
                      <th className="py-3.5 px-4">Payer</th>
                      <th className="py-3.5 px-4 text-right">Outstanding</th>
                      <th className="py-3.5 px-4 text-right">Exp Recovery</th>
                      <th className="py-3.5 px-4 text-center">Days in AR</th>
                      <th className="py-3.5 px-4">Recommended Action</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {loading ? (
                      <tr>
                        <td colSpan={9} className="py-12 text-center text-slate-400">
                          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
                          <span>Fetching claims from SQLite...</span>
                        </td>
                      </tr>
                    ) : claimsData?.items.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="py-12 text-center text-slate-400">
                          <AlertTriangle className="w-6 h-6 mx-auto text-amber-400 mb-2" />
                          <span>No claims matched the search/filter criteria.</span>
                        </td>
                      </tr>
                    ) : (
                      claimsData?.items.map((claim) => (
                        <tr 
                          key={claim.claim_id}
                          className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                          onClick={() => handleOpenDetail(claim.claim_id)}
                        >
                          <td className="py-3.5 px-4">
                            <div className="flex items-center space-x-1.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] border ${getPriorityBandBadge(claim.priority_band)}`}>
                                {claim.priority_band || 'Low'}
                              </span>
                              <span className="font-mono text-xs font-bold text-slate-300">
                                {claim.priority_score !== null && claim.priority_score !== undefined ? claim.priority_score.toFixed(1) : '—'}
                              </span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 font-mono font-bold text-blue-400">
                            {claim.claim_id}
                          </td>
                          <td className="py-3.5 px-4 text-slate-300">
                            <div className="font-medium">{claim.payer_name || claim.payer_id}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{claim.payer_id}</div>
                          </td>
                          <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-200">
                            ${claim.outstanding_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-3.5 px-4 text-right font-mono font-semibold text-emerald-400">
                            ${claim.expected_recovery !== null && claim.expected_recovery !== undefined
                              ? claim.expected_recovery.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                              : '—'}
                          </td>
                          <td className="py-3.5 px-4 text-center font-mono">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              claim.days_in_ar > 90 
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                                : claim.days_in_ar > 45 
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                                : 'bg-slate-800 text-slate-300'
                            }`}>
                              {claim.days_in_ar}d
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-slate-300">
                            {claim.recommended_action ? (
                              <span className="inline-flex items-center space-x-1 text-[11px] text-cyan-300">
                                <Send className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                                <span className="truncate max-w-[170px]">{claim.recommended_action.title}</span>
                              </span>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(claim.claim_status)}`}>
                              {claim.claim_status}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <button
                              onClick={(e) => { e.stopPropagation(); handleOpenDetail(claim.claim_id); }}
                              className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 text-[10px] font-semibold transition-all cursor-pointer"
                            >
                              <Sparkles className="w-3.5 h-3.5" />
                              <span>Inspect</span>
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {claimsData && claimsData.total_pages > 1 && (
                <div className="py-3.5 px-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <div>
                    Page <span className="text-white font-semibold">{claimsData.page}</span> of <span className="text-white font-semibold">{claimsData.total_pages.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page <= 1 || loading}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 text-slate-200 transition-colors cursor-pointer"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      <span>Previous</span>
                    </button>
                    <button
                      onClick={() => setPage(Math.min(claimsData.total_pages, page + 1))}
                      disabled={page >= claimsData.total_pages || loading}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 text-slate-200 transition-colors cursor-pointer"
                    >
                      <span>Next</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: PRIORITY CLAIMS QUEUE */}
        {activeTab === 'priority' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <Flame className="w-5 h-5 text-amber-400" />
                  <span>Financially-Aware Priority Queue & Explainability</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Formula: <code className="text-blue-400 font-mono">0.45×P(Recovery) + 0.30×P(Delay) + 0.25×NormalizedOutstanding</code>
                </p>
              </div>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
                Top Actionable Claims
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {priorityClaims.map((claim, idx) => (
                <div
                  key={claim.claim_id}
                  onClick={() => handleOpenDetail(claim.claim_id)}
                  className="rounded-2xl bg-gradient-to-br from-[#121829] to-[#0c101c] border border-slate-800 p-5 shadow-xl hover:border-blue-500/50 transition-all cursor-pointer flex flex-col justify-between space-y-4"
                >
                  <div>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-mono font-bold text-blue-400">#{idx + 1} {claim.claim_id}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] border ${getPriorityBandBadge(claim.priority_band)}`}>
                            {claim.priority_band || 'High'}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(claim.claim_status)}`}>
                            {claim.claim_status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 font-medium mt-1">{claim.payer_name} ({claim.payer_id})</p>
                      </div>

                      <div className="text-right">
                        <div className="text-[10px] uppercase text-slate-400 font-mono">Priority Score</div>
                        <div className="text-2xl font-mono font-extrabold text-amber-400">
                          {claim.priority_score?.toFixed(1) ?? '—'}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 p-3 mt-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-center">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">Outstanding</span>
                        <div className="text-xs font-mono font-bold text-slate-200 mt-0.5">
                          ${claim.outstanding_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">P(Recovery)</span>
                        <div className="text-xs font-mono font-bold text-cyan-400 mt-0.5">
                          {((claim.recovery_probability || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">Expected Rec</span>
                        <div className="text-xs font-mono font-bold text-emerald-400 mt-0.5">
                          ${claim.expected_recovery?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>

                    {claim.recommended_action && (
                      <div className="mt-3 p-2.5 rounded-xl bg-blue-950/30 border border-blue-500/30 flex items-start space-x-2">
                        <Send className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="text-[10px] uppercase tracking-wider font-bold text-blue-300">
                            Recommended Next Action:
                          </span>
                          <p className="text-xs font-semibold text-white mt-0.5">{claim.recommended_action.title}</p>
                        </div>
                      </div>
                    )}

                    {claim.explainability_reasons && claim.explainability_reasons.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-1.5">
                        <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1">
                          <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
                          <span>Why is this claim prioritized?</span>
                        </span>
                        <ul className="space-y-1 text-xs text-slate-300">
                          {claim.explainability_reasons.slice(0, 3).map((reason, rIdx) => (
                            <li key={rIdx} className="flex items-start space-x-1.5 text-[11px] text-slate-300">
                              <span className="text-blue-400 font-bold leading-none mt-1">•</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/50">
                    <span>AR Age: <strong className="text-slate-300">{claim.days_in_ar} days</strong></span>
                    <span>Follow-Ups: <strong className="text-slate-300">{claim.followup_count}</strong></span>
                    <span className="text-blue-400 font-semibold group-hover:underline">Open Workspace →</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: PAYER RESPONSE SIMULATOR (PHASE 11) */}
        {activeTab === 'simulator' && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-br from-[#0c1b24] via-[#09151e] to-[#070e14] border border-emerald-500/30 p-6 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-2">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Phase 11 — Payer Adjudication Response Simulator</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">Realistic Payer Adjudication Engine</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    Simulates 4-class adjudication outcomes (Approved Full, Approved Partial, Additional Info Required, Denial Upheld) based on ML probabilities and action quality.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Claim ID (e.g. CLM0003394)..."
                    value={simClaimId}
                    onChange={(e) => setSimClaimId(e.target.value)}
                    className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    onClick={() => handleSimulateResponse(false)}
                    disabled={loadingSimulation || !simClaimId.trim()}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:opacity-50 text-xs font-bold text-white shadow-md transition-all cursor-pointer shrink-0 flex items-center space-x-1.5"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{loadingSimulation ? 'Simulating...' : 'Simulate Response'}</span>
                  </button>
                </div>
              </div>

              {/* Scenario Presets Bar */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-400 font-medium">Test Claim Presets:</span>
                {[
                  { label: 'CO-16 Missing Info (AetnaCare)', id: 'CLM0003394' },
                  { label: 'CO-197 Prior Auth (BlueCross)', id: 'CLM0000001' },
                  { label: 'CO-50 Medical Necessity (UnitedCare)', id: 'CLM0000005' },
                  { label: 'CO-29 Timely Filing (Cigna)', id: 'CLM0000010' },
                  { label: 'CO-18 Duplicate (Humana)', id: 'CLM0000020' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => { setSimClaimId(item.id); }}
                    className={`px-3 py-1 rounded-lg border transition-all cursor-pointer text-[11px] ${
                      simClaimId === item.id
                        ? 'bg-emerald-600/20 text-emerald-300 border-emerald-500/50 font-semibold'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {/* Simulation Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate-950/80 border border-slate-800">
                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Action Type Tested</span>
                  <select
                    value={simActionType}
                    onChange={(e) => setSimActionType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Appeal">Formal Appeal Reconsideration</option>
                    <option value="Status Inquiry">Portal / EDI 276 Status Inquiry</option>
                    <option value="Resubmission">Corrected Claim Resubmission (EDI 837)</option>
                    <option value="Escalation">Call Center Supervisory Escalation</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Transmission Channel</span>
                  <select
                    value={simChannel}
                    onChange={(e) => setSimChannel(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Portal">Provider Online Portal</option>
                    <option value="Phone">Call Center Direct Line</option>
                    <option value="Email">Secure HIPAA Email</option>
                    <option value="Certified Mail">Certified Postal Mail</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Follow-Up Action Quality</span>
                  <select
                    value={simQuality}
                    onChange={(e) => setSimQuality(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="high">🌟 High (Grounded RAG Policy + Operative Notes)</option>
                    <option value="standard">⚖️ Standard (Standard Form Filing)</option>
                    <option value="low">⚠️ Low (Incomplete Exhibits / Unchecked)</option>
                  </select>
                </div>
              </div>

              {/* 4-Class Outcome Probability Distribution Meter */}
              {simProbabilities && (
                <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Calculated Payer Adjudication Probability Distribution
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400">Sums to 100%</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
                    <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-center">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase">Approved Full</span>
                      <div className="text-xl font-mono font-extrabold text-emerald-300 mt-0.5">
                        {(simProbabilities.p_approved_full * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-center">
                      <span className="text-[10px] font-semibold text-cyan-400 uppercase">Approved Partial</span>
                      <div className="text-xl font-mono font-extrabold text-cyan-300 mt-0.5">
                        {(simProbabilities.p_approved_partial * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-center">
                      <span className="text-[10px] font-semibold text-amber-400 uppercase">Additional Info</span>
                      <div className="text-xl font-mono font-extrabold text-amber-300 mt-0.5">
                        {(simProbabilities.p_additional_info_required * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-center">
                      <span className="text-[10px] font-semibold text-rose-400 uppercase">Denial Upheld</span>
                      <div className="text-xl font-mono font-extrabold text-rose-300 mt-0.5">
                        {(simProbabilities.p_denial_upheld * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Simulation Result Card */}
              {simulationResult && (
                <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${getOutcomeStyle(simulationResult.simulated_outcome).badge}`}>
                        {getOutcomeStyle(simulationResult.simulated_outcome).label}
                      </span>
                      <span className="text-xs text-slate-300 font-mono">
                        {simulationResult.claim_id} • {simulationResult.payer_name}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-xs">
                      <span className="text-slate-400">Response Turnaround:</span>
                      <strong className="text-amber-400 font-mono">{simulationResult.turnaround_days} days ({simulationResult.simulated_response_date})</strong>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] uppercase text-slate-500">Recovered Amount</span>
                      <div className="text-lg font-mono font-bold text-emerald-400 mt-0.5">
                        ${simulationResult.recovered_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] uppercase text-slate-500">Remaining Balance</span>
                      <div className="text-lg font-mono font-bold text-slate-300 mt-0.5">
                        ${simulationResult.remaining_outstanding.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] uppercase text-slate-500">New Claim Status</span>
                      <div className="text-base font-bold text-cyan-300 mt-0.5">
                        {simulationResult.new_claim_status}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] uppercase text-slate-500">Remittance Reference</span>
                      <div className="text-xs font-mono font-bold text-amber-300 mt-1 truncate">
                        {simulationResult.remittance_reference}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Official Remittance Advice / Response Readout
                    </span>
                    <p className="p-3.5 rounded-xl bg-[#060910] border border-slate-800/80 text-xs text-slate-200 leading-relaxed font-mono">
                      "{simulationResult.payer_response_text}"
                    </p>
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-xs text-slate-400">
                      {simulationResult.applied_to_db ? '✓ Committed to SQLite Database' : 'Simulated in Sandbox Mode (Not persisted)'}
                    </span>
                    {!simulationResult.applied_to_db && (
                      <button
                        onClick={() => handleSimulateResponse(true)}
                        disabled={loadingSimulation}
                        className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow transition-all cursor-pointer flex items-center space-x-1.5"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Apply & Commit Recovery to Database</span>
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: FOLLOW-UP GENERATOR STUDIO */}
        {activeTab === 'generator' && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-br from-[#12162b] via-[#0e1220] to-[#0a0d17] border border-indigo-500/30 p-6 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-2">
                    <FileCode2 className="w-3.5 h-3.5" />
                    <span>Phase 10 — Multi-Format Follow-Up Artifact Generator</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">Healthcare Follow-Up Communication Studio</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    Generate CMS-1500/UB-04 appeal letters, portal inquiries, call scripts, email templates, and EDI resubmission packets grounded in real payer rules.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Claim ID (e.g. CLM0003394)..."
                    value={genClaimId}
                    onChange={(e) => setGenClaimId(e.target.value)}
                    className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={handleGenerateArtifacts}
                    disabled={loadingGenerator || !genClaimId.trim()}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-xs font-bold text-white shadow-md transition-all cursor-pointer shrink-0 flex items-center space-x-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{loadingGenerator ? 'Compiling...' : 'Generate Artifacts'}</span>
                  </button>
                </div>
              </div>

              {/* Scenario Presets Bar */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-400 font-medium">Quick Denial Presets:</span>
                {[
                  { label: 'CO-16 Missing Info (AetnaCare)', id: 'CLM0003394' },
                  { label: 'CO-197 Prior Auth (BlueCross)', id: 'CLM0000001' },
                  { label: 'CO-50 Medical Necessity', id: 'CLM0000005' },
                  { label: 'CO-29 Timely Filing', id: 'CLM0000010' },
                  { label: 'CO-18 Duplicate Disallowance', id: 'CLM0000020' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => { setGenClaimId(item.id); }}
                    className={`px-3 py-1 rounded-lg border transition-all cursor-pointer text-[11px] ${
                      genClaimId === item.id
                        ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/50 font-semibold'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {/* Controls & Formatting Bar */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-950/80 border border-slate-800">
                <div className="md:col-span-2 space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Communication Format</span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                    {[
                      { id: 'appeal_letter', label: 'Appeal Letter' },
                      { id: 'portal_message', label: 'Portal Inquiry' },
                      { id: 'phone_script', label: 'Phone Script' },
                      { id: 'email_template', label: 'Email Template' },
                      { id: 'edi_resubmission_note', label: 'EDI 837 Packet' },
                    ].map((fmt) => (
                      <button
                        key={fmt.id}
                        onClick={() => setGenFormat(fmt.id as any)}
                        className={`py-2 px-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer text-center truncate ${
                          genFormat === fmt.id
                            ? 'bg-indigo-600 text-white shadow-md'
                            : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                      >
                        {fmt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Negotiation Tone</span>
                  <select
                    value={genTone}
                    onChange={(e) => setGenTone(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="urgent">⚡ Urgent / Expedited</option>
                    <option value="firm">⚖️ Firm / Formal Legal</option>
                    <option value="collaborative">🤝 Collaborative / Inquiry</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Custom Clinical Remarks</span>
                  <input
                    type="text"
                    value={genCustomNotes}
                    onChange={(e) => setGenCustomNotes(e.target.value)}
                    placeholder="Add custom notes..."
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Document Preview Artifact */}
              {generatedArtifacts && (
                <div className="space-y-4">
                  <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-sm font-bold text-indigo-400">{generatedArtifacts.claim_id}</span>
                          <span className="text-xs text-slate-300 font-semibold">• {generatedArtifacts.payer_name}</span>
                          {generatedArtifacts.denial_code && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              {generatedArtifacts.denial_code} ({generatedArtifacts.denial_reason})
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">
                          Grounded in: <strong className="text-emerald-400">{generatedArtifacts.grounded_policy_title}</strong>
                        </p>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => copyToClipboard(getCurrentArtifactContent())}
                          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-colors cursor-pointer"
                        >
                          {copiedMessage ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedMessage ? 'Copied to Clipboard' : 'Copy Document'}</span>
                        </button>
                      </div>
                    </div>

                    <pre className="p-4 rounded-xl bg-[#060910] border border-slate-800/80 font-mono text-[11px] leading-relaxed text-slate-200 overflow-x-auto whitespace-pre-wrap max-h-[520px] overflow-y-auto selection:bg-indigo-600">
                      {getCurrentArtifactContent()}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: AI AGENT LIVE ACTION CENTER */}
        {activeTab === 'agent' && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-br from-[#101b33] via-[#0e1628] to-[#090e1a] border border-blue-500/40 p-6 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-2">
                    <Bot className="w-3.5 h-3.5" />
                    <span>Phase 9 — Autonomous AI Follow-Up Agent</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">AI Follow-Up Decision & Action Center</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    Autonomous reasoning engine that intakes claim state, retrieves payer policy via RAG, crafts HIPAA-compliant appeal letters, and logs audit actions.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Enter Claim ID (e.g. CLM0003394)..."
                    value={agentClaimId}
                    onChange={(e) => setAgentClaimId(e.target.value)}
                    className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => handleFormulateDecision(agentClaimId)}
                    disabled={loadingAgentDecision || !agentClaimId.trim()}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:opacity-50 text-xs font-bold text-white shadow-md transition-all cursor-pointer shrink-0 flex items-center space-x-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{loadingAgentDecision ? 'Formulating...' : 'Run AI Agent'}</span>
                  </button>
                </div>
              </div>

              {agentExecutionSuccess && (
                <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex items-center space-x-2 text-emerald-300 text-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{agentExecutionSuccess}</span>
                </div>
              )}

              {/* Agent Decision & Generated Artifact */}
              {agentDecision && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left Column: Decision Matrix */}
                  <div className="space-y-4">
                    <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Agent Decision Matrix</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Confidence: {(agentDecision.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs">
                          <span className="text-slate-500">Target Claim:</span>
                          <p className="font-mono font-bold text-blue-400 mt-0.5">{agentDecision.claim_id}</p>
                        </div>
                        <div className="text-xs">
                          <span className="text-slate-500">Determined Action:</span>
                          <p className="font-bold text-white mt-0.5">{agentDecision.recommended_action}</p>
                        </div>
                        <div className="text-xs">
                          <span className="text-slate-500">Optimal Transmission Channel:</span>
                          <p className="font-medium text-cyan-300 mt-0.5">{agentDecision.channel}</p>
                        </div>
                        <div className="text-xs">
                          <span className="text-slate-500">Execution Urgency:</span>
                          <p className="font-bold text-amber-400 mt-0.5">{agentDecision.urgency}</p>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-800/80 text-xs">
                        <span className="text-slate-500">Clinical & Strategic Reasoning:</span>
                        <p className="text-slate-300 leading-relaxed mt-1 bg-slate-900/60 p-3 rounded-xl border border-slate-800/60">
                          {agentDecision.reasoning}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-slate-800/80 text-xs">
                        <span className="text-slate-500">Grounded RAG Policy Rule:</span>
                        <p className="font-semibold text-emerald-400 mt-0.5">{agentDecision.retrieved_policy_title}</p>
                        <p className="text-[11px] text-slate-400 mt-1 italic line-clamp-3">
                          "{agentDecision.retrieved_policy_snippet}"
                        </p>
                      </div>

                      {/* Action Triggers */}
                      <div className="pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row gap-2">
                        <button
                          onClick={() => handleExecuteAction(true)}
                          disabled={executingAgent}
                          className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-xs font-bold text-white shadow-md transition-all cursor-pointer flex items-center justify-center space-x-1.5"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>{executingAgent ? 'Executing...' : 'Simulate Follow-Up'}</span>
                        </button>
                        <button
                          onClick={() => handleExecuteAction(false)}
                          disabled={executingAgent}
                          className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-xs font-bold text-white shadow-md transition-all cursor-pointer flex items-center justify-center space-x-1.5"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>{executingAgent ? 'Executing...' : 'Execute Direct'}</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Generated Letter */}
                  <div className="lg:col-span-2 space-y-4">
                    <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-3 flex flex-col justify-between h-full">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div className="flex items-center space-x-2">
                          <FileText className="w-4 h-4 text-cyan-400" />
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                            Generated Communication Artifact Draft
                          </span>
                        </div>
                        <button
                          onClick={() => copyToClipboard(agentDecision.generated_message)}
                          className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors cursor-pointer"
                        >
                          {copiedMessage ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedMessage ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>

                      <pre className="p-4 rounded-xl bg-[#070b12] border border-slate-800/80 font-mono text-[11px] leading-relaxed text-slate-200 overflow-x-auto whitespace-pre-wrap max-h-[480px] overflow-y-auto">
                        {agentDecision.generated_message}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Audit Log */}
            <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                  <History className="w-4 h-4 text-cyan-400" />
                  <span>Autonomous Agent Execution Audit Trail</span>
                </h4>
                <span className="text-xs text-slate-500">Stored in SQLite agent_actions table</span>
              </div>

              {agentActionHistory.length === 0 ? (
                <div className="py-10 text-center text-slate-400 text-xs">
                  No automated actions logged yet. Run the agent on a claim above to record an action.
                </div>
              ) : (
                <div className="space-y-3">
                  {agentActionHistory.map((act) => (
                    <div
                      key={act.action_id}
                      className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-blue-400">#{act.action_id}</span>
                          <span className="font-mono font-semibold text-slate-200">{act.claim_id}</span>
                          <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-semibold">
                            {act.recommended_action}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            act.approval_status === 'EXECUTED' 
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                              : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          }`}>
                            {act.approval_status}
                          </span>
                        </div>
                        <span className="font-mono text-[11px] text-slate-500">{act.created_at}</span>
                      </div>

                      <p className="text-xs text-slate-300">{act.reasoning}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 6: PAYER POLICY RAG */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-br from-[#0f172a] via-[#101b33] to-[#0d162b] border border-blue-500/30 p-6 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-2">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Phase 8 — Payer Policy RAG Retrieval Engine</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">Semantic Payer Guidelines & Rules Search</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    TF-IDF + Cosine Similarity Vector Index over 40 structured policy documents across all 10 payers.
                  </p>
                </div>
                <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  Vector Engine: Indexed & Online
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
                <div className="relative md:col-span-3">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type="text"
                    placeholder="Search policy terms (e.g. missing documentation, peer to peer, timely filing, operative report)..."
                    value={ragQuery}
                    onChange={(e) => setRagQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleRagSearch()}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <select
                    value={ragPayerFilter}
                    onChange={(e) => setRagPayerFilter(e.target.value)}
                    className="w-full px-3 py-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="">All Payers (10 Payers)</option>
                    <option value="PAY001">PAY001 - BlueCross Health</option>
                    <option value="PAY002">PAY002 - AetnaCare</option>
                    <option value="PAY003">PAY003 - UnitedCare</option>
                    <option value="PAY004">PAY004 - Cigna Health</option>
                    <option value="PAY005">PAY005 - Medicare</option>
                    <option value="PAY006">PAY006 - Medicaid</option>
                    <option value="PAY007">PAY007 - Humana</option>
                    <option value="PAY008">PAY008 - Kaiser Health</option>
                    <option value="PAY009">PAY009 - Anthem</option>
                    <option value="PAY010">PAY010 - Molina Health</option>
                  </select>

                  <button
                    onClick={handleRagSearch}
                    disabled={loadingRag}
                    className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:opacity-50 text-xs font-bold text-white shadow-md transition-all cursor-pointer shrink-0"
                  >
                    {loadingRag ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Retrieved <strong className="text-white">{ragResults.length}</strong> matching policy chunks</span>
                <span className="font-mono text-slate-500">Algorithm: TF-IDF Vector Similarity</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {ragResults.map((chunk) => (
                  <div
                    key={chunk.chunk_id}
                    className="rounded-2xl bg-slate-900/70 border border-slate-800 p-5 shadow-lg flex flex-col justify-between space-y-3 hover:border-blue-500/40 transition-all"
                  >
                    <div>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-white">{chunk.payer_name}</span>
                            <span className="text-[10px] font-mono text-slate-500">({chunk.payer_id})</span>
                          </div>
                          <h4 className="text-sm font-bold text-blue-400 mt-1">{chunk.title}</h4>
                        </div>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-mono font-semibold">
                          Score: {(chunk.similarity_score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed mt-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                        {chunk.content}
                      </p>
                    </div>

                    <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/60 text-[11px] text-slate-400">
                      <div>
                        <span className="text-slate-500">Topic:</span>
                        <div className="font-medium text-slate-300 truncate">{chunk.topic}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">Filing Limit:</span>
                        <div className="font-medium text-amber-400">{chunk.filing_deadline_days} days</div>
                      </div>
                      <div>
                        <span className="text-slate-500">Contact:</span>
                        <div className="font-medium text-cyan-300 truncate">{chunk.preferred_contact}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: ML MODEL METRICS */}
        {activeTab === 'ml' && (
          <div className="space-y-6">
            <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-6 shadow-xl space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <BrainCircuit className="w-5 h-5 text-blue-400" />
                    <span>Real Model Evaluation Results (Test Set N=2,000)</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Trained locally on 8,000 synthetic historical claims with 24 multi-modal clinical and financial features.
                  </p>
                </div>
                <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  Version: {metrics?.model_version || '1.0.0'}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-6 shadow-lg space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      Target: was_delayed
                    </span>
                    <h4 className="text-lg font-bold text-white mt-1.5">Delay Prediction Model</h4>
                    <p className="text-xs text-slate-400">HistGradientBoostingClassifier</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 font-mono">ROC-AUC</span>
                    <div className="text-2xl font-mono font-extrabold text-blue-400">
                      {metrics?.models.delay_model.metrics.roc_auc.toFixed(4) ?? '0.7462'}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Accuracy</span>
                    <div className="text-base font-bold text-white font-mono mt-1">
                      {((metrics?.models.delay_model.metrics.accuracy || 0.792) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Precision</span>
                    <div className="text-base font-bold text-emerald-400 font-mono mt-1">
                      {((metrics?.models.delay_model.metrics.precision || 0.8207) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Recall</span>
                    <div className="text-base font-bold text-cyan-400 font-mono mt-1">
                      {((metrics?.models.delay_model.metrics.recall || 0.9305) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">F1-Score</span>
                    <div className="text-base font-bold text-indigo-400 font-mono mt-1">
                      {metrics?.models.delay_model.metrics.f1.toFixed(4) ?? '0.8722'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-6 shadow-lg space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      Target: was_denied
                    </span>
                    <h4 className="text-lg font-bold text-white mt-1.5">Denial Prediction Model</h4>
                    <p className="text-xs text-slate-400">HistGradientBoostingClassifier</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 font-mono">ROC-AUC</span>
                    <div className="text-2xl font-mono font-extrabold text-rose-400">
                      {metrics?.models.denial_model.metrics.roc_auc.toFixed(4) ?? '0.7818'}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Accuracy</span>
                    <div className="text-base font-bold text-white font-mono mt-1">
                      {((metrics?.models.denial_model.metrics.accuracy || 0.82) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Precision</span>
                    <div className="text-base font-bold text-emerald-400 font-mono mt-1">
                      {((metrics?.models.denial_model.metrics.precision || 0.6806) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">Recall</span>
                    <div className="text-base font-bold text-cyan-400 font-mono mt-1">
                      {((metrics?.models.denial_model.metrics.recall || 0.5464) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 uppercase">F1-Score</span>
                    <div className="text-base font-bold text-indigo-400 font-mono mt-1">
                      {metrics?.models.denial_model.metrics.f1.toFixed(4) ?? '0.6061'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: SYSTEM DIAGNOSTICS */}
        {activeTab === 'system' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl space-y-4">
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-400" />
                <span>Active API Endpoints & Verification</span>
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
                  <div className="text-xs font-mono font-semibold text-emerald-400 mb-1">POST /api/closed-loop/run</div>
                  <p className="text-[11px] text-slate-400">Autonomous revenue recovery loop engine.</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
                  <div className="text-xs font-mono font-semibold text-emerald-400 mb-1">POST /api/simulator/simulate</div>
                  <p className="text-[11px] text-slate-400">Payer adjudication response simulator.</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
                  <div className="text-xs font-mono font-semibold text-emerald-400 mb-1">POST /api/generator/generate</div>
                  <p className="text-[11px] text-slate-400">Multi-format follow-up compilation engine.</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
                  <div className="text-xs font-mono font-semibold text-emerald-400 mb-1">POST /api/agent/decide</div>
                  <p className="text-[11px] text-slate-400">Autonomous RAG-grounded follow-up formulation.</p>
                </div>
              </div>

              {health && (
                <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 font-mono text-xs text-slate-300">
                  <div className="text-slate-500 mb-2 border-b border-slate-800 pb-1">System Health Status ({health.status})</div>
                  <pre className="overflow-x-auto text-[11px] leading-relaxed">
                    {JSON.stringify(health, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RICH CLAIM DETAIL WORKSPACE MODAL */}
        {selectedClaimId && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
            <div className="bg-[#0c1220] border border-slate-700/80 rounded-2xl max-w-4xl w-full max-h-[92vh] overflow-y-auto shadow-2xl flex flex-col">
              {/* Modal Top Header */}
              <div className="p-6 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-[#0c1220]/95 backdrop-blur z-20">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2.5">
                      <h2 className="text-xl font-bold text-white font-mono">{selectedClaimId}</h2>
                      {claimDetail && (
                        <>
                          <span className={`px-2.5 py-0.5 rounded text-xs border ${getPriorityBandBadge(claimDetail.priority_band)}`}>
                            {claimDetail.priority_band || 'Priority'} ({claimDetail.priority_score?.toFixed(1)})
                          </span>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getStatusBadge(claimDetail.claim_status)}`}>
                            {claimDetail.claim_status}
                          </span>
                        </>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Patient: <strong className="text-slate-200 font-mono">{claimDetail?.patient_id}</strong> • Provider: <strong className="text-slate-200 font-mono">{claimDetail?.provider_id}</strong> • Payer: <strong className="text-blue-300">{claimDetail?.payer_name}</strong>
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleCloseDetail}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Sub-Navigation Bar */}
              <div className="px-6 pt-3 border-b border-slate-800/80 flex space-x-3 bg-slate-950/40">
                <button
                  onClick={() => setModalTab('strategy')}
                  className={`pb-2.5 px-2 text-xs font-semibold border-b-2 transition-all cursor-pointer flex items-center space-x-1.5 ${
                    modalTab === 'strategy'
                      ? 'border-blue-500 text-blue-400 font-bold'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Strategy & Predictions</span>
                </button>
                <button
                  onClick={() => setModalTab('clinical')}
                  className={`pb-2.5 px-2 text-xs font-semibold border-b-2 transition-all cursor-pointer flex items-center space-x-1.5 ${
                    modalTab === 'clinical'
                      ? 'border-blue-500 text-blue-400 font-bold'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Claim & Billing Metadata</span>
                </button>
                <button
                  onClick={() => setModalTab('payer')}
                  className={`pb-2.5 px-2 text-xs font-semibold border-b-2 transition-all cursor-pointer flex items-center space-x-1.5 ${
                    modalTab === 'payer'
                      ? 'border-blue-500 text-blue-400 font-bold'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Payer Policy & RAG Rules</span>
                </button>
                <button
                  onClick={() => setModalTab('timeline')}
                  className={`pb-2.5 px-2 text-xs font-semibold border-b-2 transition-all cursor-pointer flex items-center space-x-1.5 ${
                    modalTab === 'timeline'
                      ? 'border-blue-500 text-blue-400 font-bold'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <History className="w-3.5 h-3.5" />
                  <span>Follow-Up History ({claimDetail?.followups?.length || 0})</span>
                </button>
              </div>

              {/* Modal Body Content */}
              <div className="p-6 space-y-6">
                {loadingDetail || !claimDetail ? (
                  <div className="py-20 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
                    <span>Loading comprehensive claim workspace...</span>
                  </div>
                ) : (
                  <>
                    {/* MODAL TAB 1: AI STRATEGY & ML PREDICTIONS */}
                    {modalTab === 'strategy' && (
                      <div className="space-y-5">
                        {claimDetail.recommended_action && (
                          <div className="rounded-2xl bg-gradient-to-br from-[#121c33] to-[#0c1526] border border-blue-500/40 p-5 shadow-xl space-y-3">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <Send className="w-4 h-4 text-blue-400" />
                                <span className="text-xs font-bold uppercase tracking-wider text-blue-300">
                                  Autonomous AI Recommended Next Action
                                </span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                  claimDetail.recommended_action.urgency === 'Immediate' 
                                    ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                                    : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                }`}>
                                  Urgency: {claimDetail.recommended_action.urgency}
                                </span>
                                <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-cyan-300">
                                  Channel: {claimDetail.recommended_action.channel}
                                </span>
                              </div>
                            </div>

                            <div>
                              <h4 className="text-base font-bold text-white">
                                {claimDetail.recommended_action.title}
                              </h4>
                              <p className="text-xs text-slate-200 leading-relaxed mt-1.5">
                                {claimDetail.recommended_action.description}
                              </p>
                            </div>

                            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-400">
                              <strong className="text-slate-300 font-semibold">Policy Rationale: </strong>
                              {claimDetail.recommended_action.rationale}
                            </div>

                            <div className="pt-2 flex items-center justify-between">
                              <span className="text-xs text-slate-400">Open in dedicated studios:</span>
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => {
                                    setSimClaimId(claimDetail.claim_id);
                                    handleFetchSimProbabilities();
                                    handleCloseDetail();
                                    setActiveTab('simulator');
                                  }}
                                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow transition-all cursor-pointer flex items-center space-x-1"
                                >
                                  <Cpu className="w-3.5 h-3.5" />
                                  <span>Simulate Adjudication →</span>
                                </button>
                                <button
                                  onClick={() => {
                                    setGenClaimId(claimDetail.claim_id);
                                    handleGenerateArtifacts();
                                    handleCloseDetail();
                                    setActiveTab('generator');
                                  }}
                                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow transition-all cursor-pointer flex items-center space-x-1"
                                >
                                  <FileCode2 className="w-3.5 h-3.5" />
                                  <span>Generate Letters →</span>
                                </button>
                                <button
                                  onClick={() => {
                                    setAgentClaimId(claimDetail.claim_id);
                                    handleFormulateDecision(claimDetail.claim_id);
                                    handleCloseDetail();
                                    setActiveTab('agent');
                                  }}
                                  className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow transition-all cursor-pointer flex items-center space-x-1"
                                >
                                  <Bot className="w-3.5 h-3.5" />
                                  <span>AI Agent Studio →</span>
                                </button>
                              </div>
                            </div>
                          </div>
                        )}

                        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-4">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                              <BrainCircuit className="w-4 h-4 text-purple-400" />
                              <span>Machine Learning Risk & Yield Assessment</span>
                            </h4>
                            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                              Scikit-Learn Gradient Boosting
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400">Priority Score</span>
                              <div className="text-xl font-mono font-extrabold text-amber-400 mt-1">
                                {claimDetail.priority_score?.toFixed(1) ?? '—'}
                              </div>
                            </div>
                            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400">Exp Recovery</span>
                              <div className="text-xl font-mono font-extrabold text-emerald-400 mt-1">
                                ${claimDetail.expected_recovery?.toLocaleString(undefined, { minimumFractionDigits: 2 }) ?? '0.00'}
                              </div>
                            </div>
                            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400">Delay Risk P(Delay)</span>
                              <div className="text-xl font-mono font-extrabold text-blue-400 mt-1">
                                {((claimDetail.delay_probability || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400">Denial Risk P(Denial)</span>
                              <div className="text-xl font-mono font-extrabold text-rose-400 mt-1">
                                {((claimDetail.denial_probability || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </div>

                        {claimDetail.explainability_reasons && claimDetail.explainability_reasons.length > 0 && (
                          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-3">
                            <h5 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center space-x-1.5">
                              <HelpCircle className="w-4 h-4 text-amber-400" />
                              <span>Why is this claim prioritized for follow-up?</span>
                            </h5>
                            <ul className="space-y-2 text-xs text-slate-300">
                              {claimDetail.explainability_reasons.map((reason, idx) => (
                                <li key={idx} className="flex items-start space-x-2">
                                  <span className="text-amber-400 font-bold leading-none mt-1">•</span>
                                  <span>{reason}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* MODAL TAB 2: CLAIM & BILLING METADATA */}
                    {modalTab === 'clinical' && (
                      <div className="space-y-5">
                        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-3">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Financial Ledger Breakdown</h4>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Outstanding Balance</span>
                              <div className="text-base font-mono font-bold text-emerald-400 mt-0.5">
                                ${claimDetail.outstanding_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Billed Amount</span>
                              <div className="text-base font-mono font-bold text-slate-200 mt-0.5">
                                ${claimDetail.billed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Allowed Amount</span>
                              <div className="text-base font-mono font-bold text-slate-300 mt-0.5">
                                ${claimDetail.allowed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Paid Amount</span>
                              <div className="text-base font-mono font-bold text-blue-300 mt-0.5">
                                ${claimDetail.paid_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Patient Responsibility</span>
                              <div className="text-base font-mono font-bold text-amber-300 mt-0.5">
                                ${claimDetail.patient_responsibility.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                              <span className="text-[10px] uppercase text-slate-500">Expected Reimbursement</span>
                              <div className="text-base font-mono font-bold text-cyan-300 mt-0.5">
                                ${claimDetail.expected_reimbursement.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-3">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Clinical & Adjudication Metadata</h4>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                            <div>
                              <span className="text-slate-500">Claim Type:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.claim_type}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Place of Service:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.place_of_service}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Service Date:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.service_date}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Claim Date:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.claim_date}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Days in AR:</span>
                              <p className="font-semibold text-amber-400 mt-0.5">{claimDetail.days_in_ar} days</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Network Status:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.network_status}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Denial Code:</span>
                              <p className="font-mono font-bold text-rose-400 mt-0.5">{claimDetail.denial_code || 'None'}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Denial Reason:</span>
                              <p className="font-semibold text-rose-300 mt-0.5">{claimDetail.denial_reason || 'None'}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Prior Auth Status:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.authorization_status}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Appeal Status:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.appeal_status}</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Follow-Up Count:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.followup_count} attempts</p>
                            </div>
                            <div>
                              <span className="text-slate-500">Resubmissions:</span>
                              <p className="font-semibold text-slate-200 mt-0.5">{claimDetail.resubmission_count}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* MODAL TAB 3: PAYER POLICY & RAG RULES */}
                    {modalTab === 'payer' && claimDetail.payer && (
                      <div className="space-y-5">
                        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-5 space-y-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="text-base font-bold text-white">{claimDetail.payer.payer_name}</h4>
                              <p className="text-xs text-slate-400">Payer ID: <span className="font-mono text-blue-400">{claimDetail.payer.payer_id}</span> • Plan: {claimDetail.payer.plan_type}</p>
                            </div>
                            <span className="px-3 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs font-mono text-blue-400">
                              Contact: {claimDetail.payer.preferred_contact_method}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400 uppercase">Avg Processing Time</span>
                              <div className="text-lg font-mono font-bold text-slate-200 mt-1">
                                {claimDetail.payer.avg_processing_days} days
                              </div>
                            </div>
                            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400 uppercase">Avg Response Time</span>
                              <div className="text-lg font-mono font-bold text-slate-200 mt-1">
                                {claimDetail.payer.avg_response_days} days
                              </div>
                            </div>
                            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                              <span className="text-[11px] text-slate-400 uppercase">Filing Deadline</span>
                              <div className="text-lg font-mono font-bold text-amber-400 mt-1">
                                {claimDetail.payer.filing_deadline_days} days
                              </div>
                            </div>
                          </div>

                          <div className={`p-4 rounded-xl border flex items-center justify-between ${
                            (claimDetail.filing_deadline_remaining_days || 0) <= 30
                              ? 'bg-red-950/30 border-red-500/40 text-red-200'
                              : 'bg-slate-950/80 border-slate-800 text-slate-300'
                          }`}>
                            <div className="flex items-center space-x-2.5">
                              <Calendar className="w-5 h-5 text-amber-400 shrink-0" />
                              <div>
                                <span className="font-bold text-xs">Filing Deadline Countdown</span>
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                  Current AR age is {claimDetail.days_in_ar} days out of {claimDetail.payer.filing_deadline_days} days allowed.
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-mono font-extrabold text-amber-300">
                                {claimDetail.filing_deadline_remaining_days ?? 0} days remaining
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* RAG Retrieved Context Chunks */}
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h5 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-2">
                              <FileCheck className="w-4 h-4 text-emerald-400" />
                              <span>Relevant Policy Rules Retrieved via Vector RAG</span>
                            </h5>
                            <span className="text-[10px] text-slate-500 font-mono">Matched to {claimDetail.denial_reason || 'Claim Profile'}</span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {claimRagChunks.map((chunk) => (
                              <div key={chunk.chunk_id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-bold text-white">{chunk.title}</span>
                                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                    {(chunk.similarity_score * 100).toFixed(0)}% Match
                                  </span>
                                </div>
                                <p className="text-xs text-slate-300 leading-relaxed">
                                  {chunk.content}
                                </p>
                                {chunk.required_documents && (
                                  <div className="pt-2 border-t border-slate-900 text-[11px] text-slate-400">
                                    <strong className="text-slate-300">Required Docs: </strong>{chunk.required_documents}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* MODAL TAB 4: HISTORICAL FOLLOW-UP TIMELINE */}
                    {modalTab === 'timeline' && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                            <History className="w-4 h-4 text-blue-400" />
                            <span>Follow-Up Action Timeline ({claimDetail.followups?.length || 0} Events)</span>
                          </h4>
                          <span className="text-xs text-slate-500">Sorted newest first</span>
                        </div>

                        {!claimDetail.followups || claimDetail.followups.length === 0 ? (
                          <div className="py-12 text-center rounded-xl bg-slate-950 border border-slate-800/80 p-6 space-y-2">
                            <CheckCircle2 className="w-8 h-8 text-blue-500 mx-auto" />
                            <p className="text-xs font-semibold text-white">No Previous Follow-Ups Logged</p>
                            <p className="text-[11px] text-slate-400">
                              This claim is queued for its initial autonomous recovery action.
                            </p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {claimDetail.followups.map((item) => (
                              <div
                                key={item.followup_id}
                                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-colors space-y-2.5"
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-2">
                                    {getChannelIcon(item.channel)}
                                    <span className="font-semibold text-xs text-white">{item.action_type}</span>
                                    <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                                      {item.channel}
                                    </span>
                                  </div>
                                  <div className="text-right">
                                    <span className="text-xs font-mono text-slate-400">{item.followup_date}</span>
                                  </div>
                                </div>

                                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/50 whitespace-pre-line">
                                  "{item.message}"
                                </p>

                                {item.payer_response && (
                                  <div className="flex items-center justify-between pt-1 text-[11px]">
                                    <div className="text-slate-400">
                                      <strong className="text-slate-300">Payer Response: </strong>
                                      <span className="text-blue-300">{item.payer_response}</span>
                                      {item.response_date && <span className="text-slate-500 font-mono ml-1.5">({item.response_date})</span>}
                                    </div>
                                    {item.outcome && (
                                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                        item.outcome.toLowerCase().includes('positive') || item.outcome.toLowerCase().includes('resolved')
                                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                          : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                      }`}>
                                        {item.outcome}
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Claim Workspace Active • RecoverAI Model v1.0.0</span>
                <button
                  onClick={handleCloseDetail}
                  className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer font-medium"
                >
                  Close Workspace
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Pipeline Architecture Roadmap */}
        <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-6">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            RecoverAI Closed-Loop Architecture Pipeline
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-13 gap-2 text-center text-xs">
            {[
              { phase: 'P1', title: 'Foundation', status: 'completed' },
              { phase: 'P2', title: 'Data & DB', status: 'completed' },
              { phase: 'P3', title: 'Claim API', status: 'completed' },
              { phase: 'P4', title: 'ML Models', status: 'completed' },
              { phase: 'P5', title: 'Priority', status: 'completed' },
              { phase: 'P6', title: 'Dashboard', status: 'completed' },
              { phase: 'P7', title: 'Claim Detail', status: 'completed' },
              { phase: 'P8', title: 'RAG Knowledge', status: 'completed' },
              { phase: 'P9', title: 'AI Agent', status: 'completed' },
              { phase: 'P10', title: 'Generator', status: 'completed' },
              { phase: 'P11', title: 'Simulator', status: 'completed' },
              { phase: 'P12', title: 'Closed Loop', status: 'completed' },
              { phase: 'P13', title: 'Final Polish', status: 'completed' },
            ].map((step, idx) => (
              <div 
                key={idx}
                className="rounded-lg p-3 border flex flex-col items-center justify-center space-y-1 transition-all bg-emerald-500/10 border-emerald-500/30 text-emerald-300 shadow-sm"
              >
                <span className="text-[10px] font-mono text-slate-400">{step.phase}</span>
                <span className="font-semibold text-xs text-white">{step.title}</span>
                <span className="text-[10px] font-medium text-emerald-400">
                  ✓ Complete
                </span>
              </div>
            ))}
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#070b12] py-4 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AR Follow-Up AI — RecoverAI Hackathon System</span>
          <span className="font-mono text-slate-400">Closed-Loop Autonomous Revenue Recovery Platform</span>
        </div>
      </footer>
    </div>
  );
}
