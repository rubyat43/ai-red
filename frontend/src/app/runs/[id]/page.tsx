import { fetchValidationRun } from "@/lib/api";
import Link from "next/link";


export default async function RunDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = await fetchValidationRun(id);

  return (
    <div className="flex flex-col gap-16 animate-in fade-in duration-700">
      <header>
        <Link href="/runs" className="text-muted hover:text-foreground text-xs uppercase tracking-widest mb-4 inline-block font-bold">
          ← Back to Runs
        </Link>
        <h2 className="text-4xl font-black mb-2 tracking-tight">Run Details</h2>
        <p className="text-muted font-mono">{run.id}</p>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#101014] p-8">
        <div>
          <div className="text-xs text-muted font-bold tracking-widest uppercase mb-2">Version</div>
          <div className="font-mono text-lg">{run.version_id}</div>
        </div>
        <div>
          <div className="text-xs text-muted font-bold tracking-widest uppercase mb-2">Status</div>
          <div className="text-lg capitalize">{run.status}</div>
        </div>
        <div>
          <div className="text-xs text-muted font-bold tracking-widest uppercase mb-2">Decision</div>
          <div className={`text-lg font-bold ${run.decision === 'PROMOTE' ? 'text-emerald-500' : run.decision === 'ROLLBACK' ? 'text-danger' : ''}`}>
            {run.decision || 'PENDING'}
          </div>
        </div>
        <div>
          <div className="text-xs text-muted font-bold tracking-widest uppercase mb-2">Risk Score</div>
          <div className="font-mono text-lg">{run.risk_score !== null ? run.risk_score.toFixed(2) : '-'}</div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-black uppercase tracking-widest mb-6">Attack Results</h3>
        
        {run.results && run.results.length > 0 ? (
          <div className="flex flex-col gap-4">
            {run.results.map((res: any) => (
              <div key={res.id} className="bg-[#101014] p-6 border-l-4 border-transparent hover:border-[#18181b] transition-colors flex flex-col gap-4">
                <div className="flex justify-between items-center pb-4 border-b border-[#18181b]">
                  <div className="font-bold text-lg">{res.attack_name}</div>
                  <div className={`text-xs uppercase tracking-widest font-bold px-3 py-1 ${res.success ? 'bg-danger/10 text-danger' : 'bg-emerald-500/10 text-emerald-500'}`}>
                    {res.success ? 'Attack Successful (Vulnerable)' : 'Attack Failed (Secure)'}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
                  <div>
                    <div className="text-muted font-bold tracking-widest uppercase mb-2 text-xs">Prompt Payload</div>
                    <div className="font-mono bg-background p-4 text-muted whitespace-pre-wrap">{res.prompt}</div>
                  </div>
                  <div>
                    <div className="text-muted font-bold tracking-widest uppercase mb-2 text-xs">Target Response</div>
                    <div className="font-mono bg-background p-4 text-muted whitespace-pre-wrap">{res.response || 'No response'}</div>
                  </div>
                </div>
                
                {res.reasoning && (
                  <div className="mt-2">
                    <div className="text-muted font-bold tracking-widest uppercase mb-2 text-xs">Judge Reasoning</div>
                    <div className="text-sm text-foreground leading-relaxed">{res.reasoning}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[#101014] p-8 text-center text-muted">
            No attack results available yet.
          </div>
        )}
      </section>
    </div>
  );
}
