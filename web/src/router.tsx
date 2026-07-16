import { createBrowserRouter } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import DashboardPage from "./pages/DashboardPage";
import PlayerPage from "./pages/PlayerPage";
import StatisticsPage from "./pages/StatisticsPage";
import LibraryPage from "./pages/LibraryPage";
import PlaylistDetailPage from "./pages/PlaylistDetailPage";
import SettingsPage from "./pages/SettingsPage";
import NotFoundPage from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/player", element: <PlayerPage /> },
      { path: "/stats", element: <StatisticsPage /> },
      { path: "/library", element: <LibraryPage /> },
      { path: "/library/playlist/:playlistId", element: <PlaylistDetailPage /> },
      { path: "/settings", element: <SettingsPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
