import React from "react";

export default function SkeletonGold({ rows = 10 }: { rows?: number }) {
  return (
    <div className="p-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skel-gold my-2 w-full" style={{ opacity: 0.65 }} />
      ))}
    </div>
  );
}
