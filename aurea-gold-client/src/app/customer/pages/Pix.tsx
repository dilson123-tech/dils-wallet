import React from "react";
import PixPanel from "@/app/customer/components/PixPanel";
import AureaAssistantPanel from "@/app/customer/components/AureaAssistantPanel";

export default function Pix() {
  return (
    <>
      <div className="with-assistant-right">
        <div className="pix-container">
  <PixPanel />
</div>
      </div>
      <AureaAssistantPanel />
    </>
  );
}
