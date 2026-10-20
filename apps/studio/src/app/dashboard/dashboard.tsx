import Link from 'next/link';
import SessionShell from '../../components/session-shell';
import PortfolioManager from '../../components/portfolio-manager';
export default function Dashboard(){return <SessionShell><p><Link className="button secondary" href="/portfolios/ready">Choisir Creative Editorial</Link></p><PortfolioManager mode="list"/></SessionShell>;}
