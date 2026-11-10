"use client";

import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { role: "assistant", content: data.reply }]);
      } else {
        setMessages(prev => [...prev, { role: "system", content: "Error communicating with active deployment." }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: "system", content: "Network error." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] gap-8 animate-in fade-in duration-700">
      <header>
        <h2 className="text-4xl font-black mb-2 tracking-tight">Live Chat</h2>
        <p className="text-muted">Interact with the currently active production agent.</p>
      </header>

      <div className="flex-1 bg-[#101014] p-8 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto flex flex-col gap-6 mb-8 pr-4">
          {messages.length === 0 ? (
            <div className="text-muted text-center m-auto text-sm">
              Send a message to interact with the active deployment.
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`text-xs uppercase tracking-widest font-bold mb-2 ${msg.role === 'user' ? 'text-muted' : msg.role === 'system' ? 'text-danger' : 'text-accent'}`}>
                  {msg.role}
                </div>
                <div className={`p-4 max-w-[80%] text-sm ${msg.role === 'user' ? 'bg-[#18181b] text-foreground' : msg.role === 'system' ? 'bg-danger/10 text-danger' : 'bg-background text-foreground font-mono'}`}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex flex-col items-start">
              <div className="text-xs uppercase tracking-widest font-bold mb-2 text-accent">
                Assistant
              </div>
              <div className="p-4 bg-background text-muted font-mono text-sm">
                Typing...
              </div>
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} className="flex gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 bg-background text-foreground p-4 font-mono border-none outline-none focus:ring-1 focus:ring-accent"
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={loading}
            className="bg-foreground text-background px-8 py-4 font-bold uppercase tracking-widest hover:bg-muted transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
