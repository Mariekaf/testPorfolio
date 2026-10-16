"use client";
import { useState } from "react";
import { isHealthResponse } from "@portfolio/content-contracts";

type State = "idle" | "checking" | "ready" | "unavailable";
export default function HealthPanel() {
  const [state, setState] = useState<State>("idle");
  async function check() {
    setState("checking");
    try {
      const response = await fetch("/api/v1/health/ready", { cache: "no-store", signal: AbortSignal.timeout(6000) });
      const body: unknown = await response.json();
      setState(response.ok && isHealthResponse(body) && body.status === "ok" ? "ready" : "unavailable");
    } catch { setState("unavailable"); }
  }
  const labels: Record<State, string> = {
    idle: "Prêt à vérifier", checking: "Vérification en cours…",
    ready: "Backend et PostgreSQL disponibles", unavailable: "Service indisponible — vérifiez le backend et PostgreSQL",
  };
  return <section className="health" aria-labelledby="health-title">
    <div><p className="eyebrow">ÉTAT DES SERVICES</p><h2 id="health-title">Une base solide.</h2>
      <p role="status" data-state={state}>{labels[state]}</p></div>
    <button type="button" onClick={check} disabled={state === "checking"}>Vérifier la connexion <span aria-hidden="true">↗</span></button>
  </section>;
}
