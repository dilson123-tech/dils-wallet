import React from "react";

type Props = { children: React.ReactNode };
type State = { hasError: boolean; info?: string };

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(err: any) {
    return { hasError: true, info: String(err?.message || err) };
  }
  componentDidCatch(error: any, info: any) {
    console.error("[ErrorBoundary]", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 16, color: "#ffd700", background:"#000" }}>
          <h2>Falha ao renderizar a página</h2>
          <p style={{ color:"#ccc" }}>
            {this.state.info || "Erro desconhecido."}
          </p>
          <button
            onClick={() => location.reload()}
            style={{ marginTop: 12, padding: "8px 12px", cursor:"pointer" }}
          >
            Recarregar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
export default ErrorBoundary;
