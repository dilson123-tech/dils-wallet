import React from "react";
import BalanceLive from "@/app/customer/components/BalanceLive";
import TxHistoryLive from "@/app/customer/components/TxHistoryLive";
import AureaAssistant from "@/app/customer/components/AureaAssistant";

export default function Dashboard() {
  return (
    <div className="p-4 flex flex-col gap-4 lg:flex-row lg:items-start lg:gap-6 bg-[#000] min-h-screen text-white">
      <div className="flex-1 flex flex-col gap-4">
        <div
          className="rounded-2xl border border-[#2a2a2a] bg-[#0a0a0a] shadow-xl p-4"
          style={{
            background:
              "linear-gradient(160deg, rgba(15,15,15,1) 60%, rgba(45,35,10,0.35) 100%)",
          }}
        >
          <BalanceLive />
        </div>
        <div
          className="rounded-2xl border border-[#2a2a2a] bg-[#0a0a0a] shadow-xl p-4 overflow-x-auto"
          style={{
            background:
              "linear-gradient(170deg, rgba(15,15,15,1) 60%, rgba(45,35,10,0.22) 100%)",
          }}
        >
          <TxHistoryLive />
        </div>
      </div>
      <AureaAssistant />
    </div>
  );
}
