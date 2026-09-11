import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainApp from './main/App';
import LoginPage from './main/pages/LoginPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
