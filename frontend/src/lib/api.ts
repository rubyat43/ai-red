const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchDeploymentState() {
  try {
    const res = await fetch(`${API_URL}/api/deployments/state`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch deployment state");
    return await res.json();
  } catch (error) {
    console.error("fetchDeploymentState:", error);
    return {
      active_color: "blue",
      blue_version: "v1.0.0",
      blue_traffic_percent: 100,
      green_version: null,
      green_traffic_percent: 0,
      is_validating: false,
    };
  }
}

export async function fetchValidationRuns() {
  try {
    const res = await fetch(`${API_URL}/api/validation-runs`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch validation runs");
    return await res.json();
  } catch (error) {
    console.error("fetchValidationRuns:", error);
    return [];
  }
}

export async function fetchValidationRun(id: string) {
  try {
    const res = await fetch(`${API_URL}/api/validation-runs/${id}`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch validation run");
    return await res.json();
  } catch (error) {
    console.error("fetchValidationRun:", error);
    return { id, version_id: "unknown", status: "not found", decision: null, risk_score: null, results: [] };
  }
}

export async function fetchSettings() {
  try {
    const res = await fetch(`${API_URL}/api/settings`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch settings");
    return await res.json();
  } catch (error) {
    console.error("fetchSettings:", error);
    return { risk_threshold: 0.25 };
  }
}

export async function updateSettings(data: { risk_threshold: number }) {
  const res = await fetch(`${API_URL}/api/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update settings");
  return res.json();
}

export async function triggerValidationRun(versionId: string) {
  const res = await fetch(`${API_URL}/api/validation-runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version_id: versionId }),
  });
  if (!res.ok) throw new Error("Failed to trigger validation run");
  return res.json();
}

export async function fetchAgentVersions() {
  try {
    const res = await fetch(`${API_URL}/api/agent-versions`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch agent versions");
    return await res.json();
  } catch (error) {
    console.error("fetchAgentVersions:", error);
    return [];
  }
}
