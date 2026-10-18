import OperatorPanel from "@/components/operator-panel";
export default async function OperatorPage({searchParams}: {searchParams: Promise<{order?: string}>}) {
  const params = await searchParams;
  return <OperatorPanel initialId={params.order || ""}/>;
}
