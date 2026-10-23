import ReadyEditor from '../../../../components/templates/ready-editor';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <ReadyEditor id={id}/>;}
