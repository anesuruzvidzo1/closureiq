import Link from "next/link";
import data from "@/data/operators.json";

export const metadata = { title: "Explore operators · ClosureIQ" };

export default function Explore() {
  const { operators } = data;
  return (
    <>
      <nav className="nav">
        <Link className="wordmark" href="/">Closure<span>IQ</span></Link>
        <Link className="navlink" href="/">&larr; Home</Link>
      </nav>

      <main className="container">
        <h1 className="page-title">Operators</h1>
        <p className="lede">{operators.length} Alberta operators analyzed from public AER data.</p>
        <div className="grid">
          {operators.map((o) => (
            <Link key={o.slug} href={`/explore/${o.slug}`} className="op-card">
              <h3>{o.name}</h3>
              <p className="op-meta">{o.n_wells.toLocaleString()} inactive wells</p>
              <p className="op-meta">{Math.round(o.noncompliant_pct * 100)}% Directive 013 non compliant</p>
              <p className="op-meta view">View plan &rarr;</p>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
