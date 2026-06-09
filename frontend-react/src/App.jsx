import { ThemeProvider } from './context/ThemeContext';
import TopBar from './components/TopBar';
import MainContent from './components/MainContent';

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-900">
        <TopBar />
        <MainContent />
      </div>
    </ThemeProvider>
  );
}

export default App;
