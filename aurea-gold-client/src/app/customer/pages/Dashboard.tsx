import React from "react";
import BalanceLive from "@/app/customer/components/BalanceLive";
import TxHistoryLive from "@/app/customer/components/TxHistoryLive";

export default function Dashboard(){
  return (
    <div className="p-4">
      <BalanceLive />
      <TxHistoryLive />
    </div>
  );
}
