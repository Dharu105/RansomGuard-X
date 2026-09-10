import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import TopBar from "../components/TopBar.jsx";

export default function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#050914]">
      <div className="hidden lg:flex">
        <Sidebar />
      </div>
      {navOpen ? (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <button type="button" className="absolute inset-0 bg-black/50" aria-label="Close navigation" onClick={() => setNavOpen(false)} />
          <div className="relative z-50 h-full">
            <Sidebar onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setNavOpen(true)} />
        <main className="cyber-grid flex-1 overflow-auto p-4 lg:p-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
