import React from "react";
import { createRoot } from "react-dom/client";
import QuickPixButtons from "./QuickPixButtons";

const ID = "aurea-quick-pix";
let el = document.getElementById(ID);
if (!el) {
  el = document.createElement("div");
  el.id = ID;
  document.body.appendChild(el);
}
const root = createRoot(el!);
function clickSel(sel: string){ const el = document.querySelector(sel); if(el) (el as HTMLElement).click(); }
window.addEventListener("aurea:open-pix",  () => clickSel("[data-aurea=\"pix-open\"]"));
window.addEventListener("aurea:clear-pix", () => clickSel("[data-aurea=\"pix-clear\"]"));
root.render(<QuickPixButtons />);
