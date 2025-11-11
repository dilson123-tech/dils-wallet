import SummaryKpis from "@/app/customer/components/SummaryKpis";
import SummaryChart from "@/app/customer/components/SummaryChart";
import RecentPixList from "@/app/customer/components/RecentPixList";

export default function App() {
  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="px-4 md:px-6 py-4 border-b bg-white">
        <h1 className="text-xl md:text-2xl font-semibold">
          AUREA GOLD • PREMIUM <span className="text-xs font-normal opacity-70 align-middle">v1.0 beta</span>
        </h1>
      </header>

      <main className="p-4 md:p-6 space-y-4 max-w-6xl mx-auto">
        <SummaryKpis />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2"><SummaryChart /></div>
          <div className="lg:col-span-1"><RecentPixList /></div>
        </div>
      </main>
    </div>
  );
}
