/** UI capabilities only. Backend ownership, schema validation and ETags remain authoritative. */
export const PANELS = ['projects', 'sections', 'appearance'] as const;
export type Panel = typeof PANELS[number];
export const PANEL_LABELS: Record<Panel,string> = {projects:'Projets',sections:'Sections',appearance:'Apparence'};
export type PortfolioContext = {id:string;name:string;management_state:string;source_template_id:string|null;source_template_version:string|null};
export function editorPath(item:PortfolioContext):string|null {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(item.id) || item.source_template_version!=='1.0.0') return null;
  if (item.source_template_id==='creative-editorial') return `/portfolios/${item.id}/ready`;
  if (item.source_template_id==='minimal'||item.source_template_id==='editorial') return `/portfolios/${item.id}/edit`;
  return null;
}
export function readPanel(search:string):Panel|null {
  const query=new URLSearchParams(search),values=query.getAll('panel');
  return values.length===1 && PANELS.includes(values[0] as Panel)?values[0] as Panel:null;
}
export function sameEditor(from:string,to:string):boolean {
  const a=new URL(from),b=new URL(to);
  return a.origin===b.origin && a.pathname===b.pathname;
}

export function templateName(id:string|null):string {
  return id==='minimal'?'Minimal':id==='editorial'?'Editorial':id==='creative-editorial'?'Creative Editorial':id===null?'Sans template':'Template non pris en charge';
}
