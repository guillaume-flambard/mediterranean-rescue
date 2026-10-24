import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles.css";
const client = new QueryClient({ defaultOptions: { queries: { staleTime: 0, gcTime: 60000, retry: 1 } } });
const root = document.getElementById("root");
if (!root) throw Error("Application root missing");
createRoot(root).render(<StrictMode><QueryClientProvider client={client}><App /></QueryClientProvider></StrictMode>);
