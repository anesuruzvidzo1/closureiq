import Link from "next/link";
import data from "@/data/operators.json";

export default function Home() {
  const nOps = data.operators.length;
  return (
    <>
      <nav className="nav">
        <div className="wordmark">Closure<span>IQ</span></div>
        <Link className="navlink" href="/explore">Explore &rarr;</Link>
      </nav>

      <header className="hero">
        <div className="container">
          <p className="eyebrow">Alberta closure planning</p>
          <h1>Know which inactive wells to close first.</h1>
          <p className="lede">
            Directive 088 gives every Alberta operator a mandatory closure quota. ClosureIQ reads the
            public AER well data, estimates each operator&apos;s closure exposure, and estimates which
            wells to close first to retire the most risk for a given budget. Every number traces back
            to a public source.
          </p>
          <div className="cta-row">
            <Link className="btn" href="/explore">Explore {nOps} operators</Link>
            <a className="btn ghost" href="https://github.com/anesuruzvidzo1/closureiq"
               target="_blank" rel="noreferrer">View the code</a>
          </div>
        </div>
      </header>

      <section className="block">
        <div className="container">
          <p className="section-title">The problem</p>
          <h2>A mandatory closure bill, and no easy way to plan it</h2>
          <p>
            Alberta holds tens of billions in closure liability across roughly 78,000 inactive wells.
            Under Directive 088, each operator is handed a proportionate share of a $750 million annual
            closure spend and has to decide which wells to close to meet it. Most do it in spreadsheets.
          </p>
        </div>
      </section>

      <section className="block">
        <div className="container">
          <p className="section-title">What ClosureIQ does</p>
          <div className="grid">
            <div className="card">
              <h3>Rank and score</h3>
              <p>Every inactive well is scored by Directive 013 compliance, AER deemed risk, dormancy,
                 and overdue inspections, then split into near certain, watch, and reactivatable.</p>
            </div>
            <div className="card">
              <h3>Optimize the plan</h3>
              <p>An OR-Tools optimizer picks the set of wells that retires the most risk for a given
                 budget, batching closures by field area to cut mobilization cost.</p>
            </div>
            <div className="card">
              <h3>Cited to public data</h3>
              <p>Built only on the public AER Inactive Well list and published cost figures. Every
                 number is a labelled estimate, never a confidential input.</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="foot">
        <div className="container">
          <p>Independent analysis built from public AER data. Not affiliated with or endorsed by the
             Alberta Energy Regulator. Closure costs are labelled estimates only.</p>
          <p>ClosureIQ &middot; <a href="https://github.com/anesuruzvidzo1/closureiq"
             style={{ color: "var(--accent)" }}>github.com/anesuruzvidzo1/closureiq</a></p>
        </div>
      </footer>
    </>
  );
}
