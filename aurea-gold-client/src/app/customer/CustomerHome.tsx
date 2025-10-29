import React from "react";
import AureaAssistant from "./components/AureaAssistant";

export default function CustomerHome() {
  return (
    <main
      style={{
        minHeight: "100vh",
        backgroundColor: "#000",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "40px 16px",
      }}
    >
      <AureaAssistant />
    </main>
  );
}
