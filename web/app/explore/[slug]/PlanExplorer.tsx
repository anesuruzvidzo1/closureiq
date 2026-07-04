"use client";
import { useState } from "react";

type Side = { wells: number; areas: number; risk: number; spend: number };
type Scenario = { budget: number; optimizer: Side; naive: Side };

const money = (x: number) => "$" + x.toLocaleString();
const M = (x: number) => "$" + Math.round(x / 1e6) + "M";

function Metric({ l, v }: { l: string; v: string }) {
  return (
    <div className="metric">
      <span>{l}</span>
      <span className="v">{v}</span>
    </div>
  );
}

function Bar({ label, val, max, muted }: { label: string; val: number; max: number; muted?: boolean }) {
  return (
    <div className="bar-row">
      <span className="bar-l">{label}</span>
      <span className="bar-track">
        <span className={"bar-fill" + (muted ? " muted" : "")} style={{ width: `${(val / max) * 100}%` }} />
      </span>
      <span className="bar-v">{val.toLocaleString()}</span>
    </div>
  );
}

export default function PlanExplorer({ scenarios }: { scenarios: Scenario[] }) {
  const [i, setI] = useState(Math.min(2, scenarios.length - 1));
  const s = scenarios[i];
  const { optimizer: opt, naive } = s;
  const maxRisk = Math.max(opt.risk, naive.risk) || 1;
  const dRisk = opt.risk - naive.risk;
  const dWells = opt.wells - naive.wells;

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="sec" style={{ margin: 0 }}>Optimized closure plan</h2>
        <div className="budget">{M(s.budget)} budget</div>
      </div>

      <input
        className="slider"
        type="range"
        min={0}
        max={scenarios.length - 1}
        step={1}
        value={i}
        onChange={(e) => setI(Number(e.target.value))}
        aria-label="Closure budget"
      />
      <div className="ticks">
        {scenarios.map((sc, idx) => (
          <span key={idx} className={idx === i ? "on" : ""}>{M(sc.budget)}</span>
        ))}
      </div>

      <div className="compare">
        <div className="col">
          <div className="col-h">Straight down the list</div>
          <Metric l="Wells closed" v={naive.wells.toLocaleString()} />
          <Metric l="Areas mobilized" v={String(naive.areas)} />
          <Metric l="Risk retired" v={naive.risk.toLocaleString()} />
          <Metric l="Spend" v={money(naive.spend)} />
        </div>
        <div className="col opt">
          <div className="col-h">ClosureIQ optimizer</div>
          <Metric l="Wells closed" v={opt.wells.toLocaleString()} />
          <Metric l="Areas mobilized" v={String(opt.areas)} />
          <Metric l="Risk retired" v={opt.risk.toLocaleString()} />
          <Metric l="Spend" v={money(opt.spend)} />
        </div>
      </div>

      <div className="bars">
        <Bar label="Naive" val={naive.risk} max={maxRisk} muted />
        <Bar label="Optimizer" val={opt.risk} max={maxRisk} />
      </div>

      {dRisk > 0 ? (
        <p className="win">
          Same {M(s.budget)} budget: <b>{dRisk.toLocaleString()} more risk retired</b>
          {dWells > 0 ? ` and ${dWells} more wells closed` : ""} by batching into {opt.areas} area
          {opt.areas !== 1 ? "s" : ""} instead of {naive.areas}.
        </p>
      ) : (
        <p className="win">
          At this budget the optimizer matches the naive plan. The batching edge grows for more
          geographically scattered inventories.
        </p>
      )}
    </section>
  );
}
