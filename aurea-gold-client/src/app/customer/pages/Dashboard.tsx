import SummaryKpis from "@/app/customer/components/SummaryKpis";
import SummaryChart from "@/app/customer/components/SummaryChart";
import RecentPixList from "@/app/customer/components/RecentPixList";

export default function Dashboard(){
  return (
    <div className="p-4 md:p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Aurea Gold — Resumo</h1>
      <SummaryKpis />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2"><SummaryChart /></div>
        <div className="lg:col-span-1"><RecentPixList /></div>
      </div>
    </div>
  );
}
