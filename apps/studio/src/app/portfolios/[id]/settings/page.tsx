import PortfolioManager from '../../../../components/portfolio-manager';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <PortfolioManager mode="settings" id={id}/>;}
