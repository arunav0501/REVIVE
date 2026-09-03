import type { 
  HealthStatus, 
  DbHealthCheck, 
  PaginatedClaims, 
  ClaimDetail, 
  ClaimItem,
  MLMetricsResponse,
  PredictionResult,
  DashboardMetrics,
  AgingBucket,
  PayerPerformance,
  DenialReasonItem,
  PriorityDistributionItem,
  PolicyChunk,
  RAGSearchResponse,
  AgentDecision,
  AgentActionItem,
  GeneratedArtifacts,
  OutcomeProbabilityDistribution,
  SimulationResultResponse,
  BatchSimulationResponse,
  ClosedLoopRunResponse,
  ClosedLoopSummary,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Failed to fetch health status: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDbHealth(): Promise<DbHealthCheck> {
  const res = await fetch(`${API_BASE}/api/health/db`);
  if (!res.ok) {
    throw new Error(`Failed to fetch database health: ${res.statusText}`);
  }
  return res.json();
}

export interface ClaimQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  payer_id?: string;
  claim_status?: string;
  denial_status?: string;
  claim_type?: string;
  priority_band?: string;
  min_outstanding?: number;
  max_outstanding?: number;
  min_days_ar?: number;
  max_days_ar?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export async function fetchClaims(params: ClaimQueryParams = {}): Promise<PaginatedClaims> {
  const query = new URLSearchParams();
  if (params.page) query.append('page', params.page.toString());
  if (params.page_size) query.append('page_size', params.page_size.toString());
  if (params.search) query.append('search', params.search);
  if (params.payer_id) query.append('payer_id', params.payer_id);
  if (params.claim_status) query.append('claim_status', params.claim_status);
  if (params.denial_status) query.append('denial_status', params.denial_status);
  if (params.claim_type) query.append('claim_type', params.claim_type);
  if (params.priority_band) query.append('priority_band', params.priority_band);
  if (params.min_outstanding !== undefined && params.min_outstanding !== null) {
    query.append('min_outstanding', params.min_outstanding.toString());
  }
  if (params.max_outstanding !== undefined && params.max_outstanding !== null) {
    query.append('max_outstanding', params.max_outstanding.toString());
  }
  if (params.min_days_ar !== undefined && params.min_days_ar !== null) {
    query.append('min_days_ar', params.min_days_ar.toString());
  }
  if (params.max_days_ar !== undefined && params.max_days_ar !== null) {
    query.append('max_days_ar', params.max_days_ar.toString());
  }
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.sort_order) query.append('sort_order', params.sort_order);

  const res = await fetch(`${API_BASE}/api/claims?${query.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch claims: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchClaimDetail(claimId: string): Promise<ClaimDetail> {
  const res = await fetch(`${API_BASE}/api/claims/${encodeURIComponent(claimId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch claim ${claimId}: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPriorityClaims(limit: number = 20, payerId?: string, priorityBand?: string): Promise<ClaimItem[]> {
  const query = new URLSearchParams();
  query.append('limit', limit.toString());
  if (payerId) query.append('payer_id', payerId);
  if (priorityBand) query.append('priority_band', priorityBand);

  const res = await fetch(`${API_BASE}/api/claims/priority?${query.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch priority claims: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchModelMetrics(): Promise<MLMetricsResponse> {
  const res = await fetch(`${API_BASE}/api/predictions/metrics`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ML metrics: ${res.statusText}`);
  }
  return res.json();
}

export async function predictClaim(claimId: string): Promise<PredictionResult> {
  const res = await fetch(`${API_BASE}/api/predictions/${encodeURIComponent(claimId)}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to predict claim ${claimId}: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE}/api/dashboard/metrics`);
  if (!res.ok) {
    throw new Error(`Failed to fetch dashboard metrics: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAgingBuckets(): Promise<AgingBucket[]> {
  const res = await fetch(`${API_BASE}/api/dashboard/aging`);
  if (!res.ok) {
    throw new Error(`Failed to fetch aging buckets: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPayerPerformance(): Promise<PayerPerformance[]> {
  const res = await fetch(`${API_BASE}/api/dashboard/payer-performance`);
  if (!res.ok) {
    throw new Error(`Failed to fetch payer performance: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDenialReasons(): Promise<DenialReasonItem[]> {
  const res = await fetch(`${API_BASE}/api/dashboard/denial-reasons`);
  if (!res.ok) {
    throw new Error(`Failed to fetch denial reasons: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPriorityDistribution(): Promise<PriorityDistributionItem[]> {
  const res = await fetch(`${API_BASE}/api/dashboard/priority-distribution`);
  if (!res.ok) {
    throw new Error(`Failed to fetch priority distribution: ${res.statusText}`);
  }
  return res.json();
}

export async function searchPolicyKnowledge(query: string, payerId?: string, topK: number = 4): Promise<RAGSearchResponse> {
  const params = new URLSearchParams();
  params.append('query', query);
  if (payerId) params.append('payer_id', payerId);
  params.append('top_k', topK.toString());

  const res = await fetch(`${API_BASE}/api/rag/search?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to search policy knowledge base: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchClaimPolicyContext(claimId: string): Promise<PolicyChunk[]> {
  const res = await fetch(`${API_BASE}/api/rag/claim-context/${encodeURIComponent(claimId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch claim policy context: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAgentDecision(claimId: string): Promise<AgentDecision> {
  const res = await fetch(`${API_BASE}/api/agent/decide/${encodeURIComponent(claimId)}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to formulate agent decision: ${res.statusText}`);
  }
  return res.json();
}

export async function executeAgentAction(
  claimId: string,
  simulate: boolean = true,
  customMessage?: string,
  overrideChannel?: string,
): Promise<AgentActionItem> {
  const res = await fetch(`${API_BASE}/api/agent/execute/${encodeURIComponent(claimId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      simulate,
      custom_message: customMessage,
      override_channel: overrideChannel,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to execute agent action: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAgentActions(limit: number = 20, claimId?: string): Promise<AgentActionItem[]> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (claimId) params.append('claim_id', claimId);

  const res = await fetch(`${API_BASE}/api/agent/actions?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch agent actions: ${res.statusText}`);
  }
  return res.json();
}

export async function generateArtifacts(
  claimId: string,
  artifactType: string = 'all',
  tone: string = 'firm',
  customNotes?: string,
): Promise<GeneratedArtifacts> {
  const res = await fetch(`${API_BASE}/api/generator/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      claim_id: claimId,
      artifact_type: artifactType,
      tone,
      custom_notes: customNotes,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to generate follow-up artifacts: ${res.statusText}`);
  }
  return res.json();
}

export async function previewArtifacts(claimId: string, tone: string = 'firm'): Promise<GeneratedArtifacts> {
  const params = new URLSearchParams();
  params.append('tone', tone);

  const res = await fetch(`${API_BASE}/api/generator/preview/${encodeURIComponent(claimId)}?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to preview claim artifacts: ${res.statusText}`);
  }
  return res.json();
}

export async function simulatePayerResponse(
  claimId: string,
  actionType: string = 'Appeal',
  channel: string = 'Portal',
  actionQuality: string = 'high',
  applyToDb: boolean = false,
): Promise<SimulationResultResponse> {
  const res = await fetch(`${API_BASE}/api/simulator/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      claim_id: claimId,
      action_type: actionType,
      channel,
      action_quality: actionQuality,
      apply_to_db: applyToDb,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to simulate payer response: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchOutcomeProbabilities(
  claimId: string,
  actionType: string = 'Appeal',
  actionQuality: string = 'high',
): Promise<OutcomeProbabilityDistribution> {
  const params = new URLSearchParams();
  params.append('action_type', actionType);
  params.append('action_quality', actionQuality);

  const res = await fetch(`${API_BASE}/api/simulator/probabilities/${encodeURIComponent(claimId)}?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch outcome probabilities: ${res.statusText}`);
  }
  return res.json();
}

export async function simulateBatchResponses(
  claimIds: string[],
  actionType: string = 'Appeal',
  applyToDb: boolean = false,
): Promise<BatchSimulationResponse> {
  const res = await fetch(`${API_BASE}/api/simulator/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      claim_ids: claimIds,
      action_type: actionType,
      apply_to_db: applyToDb,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to simulate batch responses: ${res.statusText}`);
  }
  return res.json();
}

export async function runClosedLoopRecovery(
  batchSize: number = 10,
  minPriorityBand: string = 'High',
  payerId?: string,
  actionQuality: string = 'high',
): Promise<ClosedLoopRunResponse> {
  const res = await fetch(`${API_BASE}/api/closed-loop/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      batch_size: batchSize,
      min_priority_band: minPriorityBand,
      payer_id: payerId || undefined,
      action_quality: actionQuality,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to execute closed-loop recovery: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchClosedLoopSummary(): Promise<ClosedLoopSummary> {
  const res = await fetch(`${API_BASE}/api/closed-loop/summary`);
  if (!res.ok) {
    throw new Error(`Failed to fetch closed-loop summary: ${res.statusText}`);
  }
  return res.json();
}
