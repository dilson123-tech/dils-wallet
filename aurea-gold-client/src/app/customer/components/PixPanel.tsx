import AureaSuperPanelMount from "./AureaSuperPanelMount";
import PixActions from "./PixActions";
import QuickPixButtons from "./QuickPixButtons";

import React, { useState } from "react";
import "./pix-panel.css";
import SkeletonGold from "./SkeletonGold";
import SummaryKpis from "./SummaryKpis";
import RecentPixList from "./RecentPixList";

export default function PixPanel() {
  const [loadingPix] = useState(false);

  return (
  <AureaSuperPanelMount />
);
}
