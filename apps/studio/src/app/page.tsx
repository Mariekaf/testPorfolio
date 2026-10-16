import HealthPanel from "./health-panel";

export default function Page() {
  return <main>
    <header><span className="brand">studio <span aria-hidden="true">✳</span></span><span className="tag">CORE-001</span></header>
    <section className="intro">
      <p className="eyebrow">LES FONDATIONS DU FUTUR STUDIO</p>
      <h1>Un nouveau départ.<br /><em>Le même soin du détail.</em></h1>
      <p>Le socle SaaS est en préparation, à côté du CMS existant. Cette page vérifie uniquement les services techniques.</p>
    </section>
    <HealthPanel />
    <aside><h2>Ce qui viendra ensuite</h2><p>Comptes, portfolios et outils de création seront ajoutés dans les tickets suivants, après validation. Aucun contenu personnel n’est migré ici.</p></aside>
    <footer>Fondations parallèles · Aucune publication de portfolio depuis ce studio</footer>
  </main>;
}
