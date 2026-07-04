import { notFound } from "next/navigation";
import Link from "next/link";
import data from "@/data/operators.json";
import PlanExplorer from "./PlanExplorer";

export function generateStaticParams() {
  return data.operators.map((o) => ({ slug: o.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const op = data.operators.find((o) => o.slug === params.slug);
  return { title: op ? `${op.name} · ClosureIQ` : "ClosureIQ" };
}

const M = (x: number) => "$" + Math.round(x / 1e6) + "M";
const money = (x: number) => "$" + x.toLocaleString();

export default function OperatorPage({ params }: { params: { slug: string } }) {
  const op = data.operators.find((o) => o.slug === params.slug);
  if (!op) notFound();

  const maxGeo = Math.max(...op.geography.map((g) => g.count));

  return (
    <>
      <nav className="nav">
        <Link className="wordmark" href="/">Closure<span>IQ</span></Link>
        <Link className="navlink" href="/explore">&larr; All operators</Link>
      </nav>

      <main className="container">
        <h1 className="page-title">{op.name}</h1>
        <p className="lede">
          {op.n_wells.toLocaleString()} inactive wells &middot; as of {data.generated}
        </p>

        <div className="stat-row">
          <div className="stat"><div className="num">{Math.round(op.noncompliant_pct * 100)}%</div><div className="lbl">Directive 013 non compliant</div></div>
          <div className="stat"><div className="num">{op.near_certain.toLocaleString()}</div><div className="lbl">Near certain closures</div></div>
          <div className="stat"><div className="num">{op.overdue.toLocaleString()}</div><div className="lbl">Inspections overdue</div></div>
          <div className="stat"><div className="num">{M(op.liability.base)}</div><div className="lbl">Est. liability (base)</div></div>
        </div>

        <PlanExplorer scenarios={op.scenarios} />

        <h2 className="sec">Where the wells are</h2>
        <div className="geo">
          {op.geography.map((g) => (
            <div key={g.area} className="geo-row">
              <span>{g.area}</span>
              <span className="geo-bar"><span style={{ width: `${(g.count / maxGeo) * 100}%` }} /></span>
              <span className="geo-n">{g.count.toLocaleString()}</span>
            </div>
          ))}
        </div>

        <h2 className="sec">Highest priority wells</h2>
        <table className="data">
          <thead>
            <tr>
              <th>Licence</th><th>Field centre</th><th>Risk</th><th>D013</th>
              <th className="r">Yrs dormant</th><th className="r">Score</th>
            </tr>
          </thead>
          <tbody>
            {op.top_wells.map((w, idx) => (
              <tr key={idx}>
                <td>{w.licence}</td><td>{w.area}</td><td>{w.risk}</td><td>{w.d013}</td>
                <td className="r">{w.yrs_dormant ?? "n/a"}</td><td className="r">{w.score}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="disc">{data.disclaimer}</p>
        <p className="disc">
          Closure costs are illustrative estimates: {money(data.cost_model.variable)} per well plus a
          one-time {money(data.cost_model.mobilization)} mobilization per field area. The optimizer
          maximizes risk retired per dollar; real closure programs also weigh area access and
          spreading work across the inventory.
        </p>
      </main>
    </>
  );
}
