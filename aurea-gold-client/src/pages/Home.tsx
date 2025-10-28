import React from "react";
import PixPanel from "../components/PixPanel";

export default function Home() {
  return (
    <main className="min-h-screen w-full bg-gradient-to-b from-black via-[#0a0a0a] to-[#1a1200] text-white flex justify-center p-4">
      <div className="w-full max-w-md">
        <PixPanel />
      </div>
    </main>
  );
}
