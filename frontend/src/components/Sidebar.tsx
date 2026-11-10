import Link from "next/link";

export function Sidebar() {
  return (
    <div className="w-72 bg-background text-muted flex flex-col justify-between py-12 px-10 h-screen sticky top-0 shrink-0">
      <div>
        <h1 className="text-2xl font-black text-foreground mb-16 uppercase tracking-[0.2em]">
          AI Red
        </h1>
        <nav className="flex flex-col gap-8 text-sm">
          <Link href="/" className="hover:text-foreground transition-colors font-semibold tracking-wide">
            DASHBOARD
          </Link>
          <Link href="/runs" className="hover:text-foreground transition-colors font-semibold tracking-wide">
            VALIDATION RUNS
          </Link>
          <Link href="/settings" className="hover:text-foreground transition-colors font-semibold tracking-wide">
            SETTINGS
          </Link>
          <Link href="/chat" className="hover:text-accent transition-colors font-semibold tracking-wide mt-8">
            LIVE CHAT
          </Link>
        </nav>
      </div>
      <div className="text-[10px] font-mono uppercase tracking-[0.3em] opacity-40">
        Status: Online
      </div>
    </div>
  );
}
