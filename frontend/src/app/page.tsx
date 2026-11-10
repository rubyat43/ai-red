import { fetchDeploymentState } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";


export default async function DashboardPage() {
  const state = await fetchDeploymentState();

  return (
    <div className="flex flex-col gap-16 animate-in fade-in duration-700">
      <header>
        <h2 className="text-4xl font-black mb-2 tracking-tight">System Dashboard</h2>
        <p className="text-muted">Current deployment status and metrics.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-[#101014] p-8">
          <div className="text-sm text-muted font-bold tracking-[0.2em] uppercase mb-4">Active Deployment</div>
          <div className="text-5xl font-black mb-4 flex items-center gap-4">
            <span className={state.active_color === 'blue' ? 'text-accent' : 'text-emerald-500'}>
              {state.active_color.toUpperCase()}
            </span>
          </div>
          <div className="flex flex-col gap-4 mt-8">
            <div className="flex justify-between items-center text-sm border-b border-[#18181b] pb-4">
              <span className="text-muted font-medium">Blue Version</span>
              <span className="font-mono">{state.blue_version} <span className="text-muted">({state.blue_traffic_percent}%)</span></span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted font-medium">Green Version</span>
              <span className="font-mono">{state.green_version || 'None'} <span className="text-muted">({state.green_traffic_percent}%)</span></span>
            </div>
          </div>
        </div>
        
        <div className="bg-[#101014] p-8 flex flex-col justify-between">
          <div>
            <div className="text-sm text-muted font-bold tracking-[0.2em] uppercase mb-4">Actions</div>
            <p className="text-sm text-muted mb-6 leading-relaxed">Initiate a new validation run to test an agent version against the AI Red Team framework. If it passes the threshold, it will be promoted to production.</p>
          </div>
          <Link href="/runs" className="bg-foreground text-background px-6 py-4 text-center font-bold uppercase tracking-widest hover:bg-muted transition-colors text-sm">
            Manage Validation Runs
          </Link>
        </div>
      </section>
    </div>
  );
}
