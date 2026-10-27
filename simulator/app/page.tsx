"use client";

import dynamic from "next/dynamic";

// cela aplikace bezi jen v prohlizeci (graf, WebSocket, localStorage)
const App = dynamic(() => import("@/components/App"), {
  ssr: false,
  loading: () => <div className="loading">Spouštím simulátor…</div>,
});

export default function Page() {
  return <App />;
}
