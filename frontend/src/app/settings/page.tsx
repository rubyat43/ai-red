import { fetchSettings, updateSettings } from "@/lib/api";
import { revalidatePath } from "next/cache";

export const dynamic = "force-dynamic";


export default async function SettingsPage() {
  const settings = await fetchSettings();

  async function saveSettings(formData: FormData) {
    "use server";
    const riskThreshold = parseFloat(formData.get("risk_threshold") as string);
    if (!isNaN(riskThreshold)) {
      await updateSettings({ risk_threshold: riskThreshold });
      revalidatePath("/settings");
    }
  }

  return (
    <div className="flex flex-col gap-16 animate-in fade-in duration-700">
      <header>
        <h2 className="text-4xl font-black mb-2 tracking-tight">System Settings</h2>
        <p className="text-muted">Configure Red Team parameters and security thresholds.</p>
      </header>

      <section className="max-w-2xl">
        <form action={saveSettings} className="bg-[#101014] p-8 flex flex-col gap-8">
          <div>
            <label className="block text-sm text-muted font-bold tracking-widest uppercase mb-4">Risk Threshold</label>
            <input 
              type="number" 
              step="0.01" 
              min="0" 
              max="1"
              name="risk_threshold" 
              defaultValue={settings.risk_threshold} 
              className="w-full bg-background text-foreground text-xl p-4 font-mono border-none outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="text-sm text-muted mt-4 leading-relaxed">
              The maximum acceptable risk score (0.0 to 1.0) for a candidate version to be promoted. 
              A risk score is the weighted average of successful attack severities. 
              Currently, default is 0.25.
            </p>
          </div>

          <button type="submit" className="bg-foreground text-background px-6 py-4 font-bold uppercase tracking-widest hover:bg-muted transition-colors self-start">
            Save Configuration
          </button>
        </form>
      </section>
    </div>
  );
}
