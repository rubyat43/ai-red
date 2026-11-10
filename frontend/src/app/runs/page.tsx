import { fetchValidationRuns, fetchAgentVersions, triggerValidationRun } from "@/lib/api";
import Link from "next/link";
import { revalidatePath } from "next/cache";

export const dynamic = "force-dynamic";


export default async function RunsPage() {
  const runs = await fetchValidationRuns();
  const versions = await fetchAgentVersions();

  async function triggerRun(formData: FormData) {
    "use server";
    const versionId = formData.get("version_id") as string;
    if (versionId) {
      await triggerValidationRun(versionId);
      revalidatePath("/runs");
    }
  }

  return (
    <div className="flex flex-col gap-16 animate-in fade-in duration-700">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-4xl font-black mb-2 tracking-tight">Validation Runs</h2>
          <p className="text-muted">History of AI Red Team security validations.</p>
        </div>
        
        <form action={triggerRun} className="flex gap-4 items-end">
          <div className="flex flex-col">
            <label className="text-xs text-muted tracking-widest uppercase mb-2">Target Version</label>
            <select name="version_id" className="bg-[#101014] text-foreground p-3 border-none outline-none min-w-[200px]">
              {versions.map((v: any) => (
                <option key={v.version_id} value={v.version_id}>{v.version_id}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="bg-foreground text-background px-6 py-3 font-bold uppercase tracking-widest hover:bg-muted transition-colors">
            Start Run
          </button>
        </form>
      </header>

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-5 text-xs text-muted font-bold tracking-widest uppercase pb-2 border-b border-[#18181b]">
          <div>Version</div>
          <div>Status</div>
          <div>Decision</div>
          <div>Risk Score</div>
          <div className="text-right">Action</div>
        </div>
        
        {runs.map((run: any) => (
          <div key={run.id} className="grid grid-cols-5 items-center bg-[#101014] p-4 text-sm hover:bg-[#15151a] transition-colors">
            <div className="font-mono">{run.version_id}</div>
            <div>
              <span className={`px-2 py-1 text-[10px] uppercase tracking-widest ${run.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' : run.status === 'running' ? 'bg-accent/10 text-accent' : 'bg-muted/10 text-muted'}`}>
                {run.status}
              </span>
            </div>
            <div className="font-bold">
              {run.decision ? (
                <span className={run.decision === 'PROMOTE' ? 'text-emerald-500' : 'text-danger'}>{run.decision}</span>
              ) : <span className="text-muted">-</span>}
            </div>
            <div className="font-mono">{run.risk_score !== null ? run.risk_score.toFixed(2) : '-'}</div>
            <div className="text-right">
              <Link href={`/runs/${run.id}`} className="text-accent hover:text-blue-400 font-bold uppercase tracking-widest text-xs">
                View Details
              </Link>
            </div>
          </div>
        ))}

        {runs.length === 0 && (
          <div className="text-center py-16 text-muted">
            No validation runs found. Start one above.
          </div>
        )}
      </div>
    </div>
  );
}
