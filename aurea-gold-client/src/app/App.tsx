import { BrowserRouter } from "react-router-dom";
import { SessionProvider } from "./context/SessionContext";
import Home from "./routes/Home";

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    </SessionProvider>
  );
}
