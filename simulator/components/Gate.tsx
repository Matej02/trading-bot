"use client";

import { useState, type FormEvent } from "react";
import { apiLogin } from "@/lib/remote";
import type { Bot } from "@/lib/bot";

const money = (v: number) => `${v.toLocaleString("cs-CZ", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} $`;

/** Obrazovky pred simulatorem: prihlaseni, nahrani dat z prohlizece, chyba. */
export default function Gate({ bot }: { bot: Bot }) {
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  if (bot.phase === "loading") return <div className="loading">Načítám data…</div>;

  if (bot.phase === "login") {
    const submit = async (e: FormEvent) => {
      e.preventDefault();
      setBusy(true);
      setErr("");
      const r = await apiLogin(password);
      setBusy(false);
      if (r.status === 200) {
        setPassword("");
        bot.init();
      } else setErr(r.data.error ?? "Přihlášení se nepovedlo.");
    };
    return (
      <div className="gate">
        <form className="gate-card" onSubmit={submit}>
          <h2>Simulátor obchodování</h2>
          <p className="muted small">Po přihlášení uvidíš stejný účet a celý deník na počítači i na mobilu.</p>
          <input type="password" autoFocus autoComplete="current-password" placeholder="Heslo"
            value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="activate go" disabled={busy || !password}>{busy ? "Přihlašuji…" : "Přihlásit"}</button>
          {err && <div className="down small">{err}</div>}
        </form>
      </div>
    );
  }

  if (bot.phase === "import" && bot.importInfo) {
    const i = bot.importInfo;
    return (
      <div className="gate">
        <div className="gate-card">
          <h2>Na serveru zatím nic není</h2>
          <p>
            V tomhle prohlížeči máš uložený účet: balance <b>{money(i.balance)}</b>, {i.journal} záznamů v deníku
            a {i.closed} uzavřených obchodů.
          </p>
          <p className="muted small">Po nahrání ho uvidíš všude, kde se přihlásíš. Účty z jiných prohlížečů se nespojí – nahraj ten, který chceš mít.</p>
          <button className="activate go" onClick={() => bot.importLocal()}>Nahrát na server</button>
          <button className="btn" onClick={() => bot.startFresh()}>Začít znovu se 100 000 $</button>
        </div>
      </div>
    );
  }

  return (
    <div className="gate">
      <div className="gate-card">
        <h2>Data se nepodařilo načíst</h2>
        <p className="down">{bot.syncNote}</p>
        <button className="activate go" onClick={() => bot.init()}>Zkusit znovu</button>
      </div>
    </div>
  );
}
