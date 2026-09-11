import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainApp from './main/App';
import LoginPage from './main/pages/LoginPage';
import SharePage from './main/pages/SharePage';
import RequireAuth from './app/RequireAuth';
import AppShell from './app/AppShell';
import Overview from './app/pages/Overview';
import MyGames from './app/pages/MyGames';
import GameDetail from './app/pages/GameDetail';
import Recaps from './app/pages/Recaps';
import Media from './app/pages/Media';
import CloudSharing from './app/pages/CloudSharing';
import Settings from './app/pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<Navigate to="/app" replace />} />
        <Route path="/settings" element={<Navigate to="/app/settings" replace />} />
        <Route path="/share/:shareId" element={<SharePage />} />
        <Route path="/app" element={<RequireAuth>{(user) => <AppShell user={user} />}</RequireAuth>}>
          <Route index element={<Overview />} />
          <Route path="games" element={<MyGames />} />
          <Route path="games/:slug" element={<GameDetail />} />
          <Route path="recaps" element={<Recaps />} />
          <Route path="media" element={<Media />} />
          <Route path="sharing" element={<CloudSharing />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
