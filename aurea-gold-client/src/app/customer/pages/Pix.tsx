import PixAISummary from "@/app/customer/components/PixAISummary";
import PixPanel from "@/app/customer/components/PixPanel";

export default function Pix() {
  return (
    <>
      <PixAISummary hours={24} />
      <div style={{ height: 12 }} />
      <PixPanel />
    </>
  );
}
