
import { ForexAdvancedPipeline } from './components/features/market/ForexAdvancedPipeline'
import { Login } from './components/auth/Login'
import { useAuth } from './context/AuthContext'
import './index.css'

function App() {
  const { isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return <div className="loading-screen gradient-text">Initializing Secure Connection...</div>;
  }

  return (
    <>
      {isAuthenticated ? (
        <div style={{ position: 'relative' }}>
          <button 
            onClick={logout} 
            className="premium-button" 
            style={{ position: 'absolute', top: '1rem', right: '1rem', zIndex: 100 }}
          >
            Logout
          </button>
          <ForexAdvancedPipeline />
        </div>
      ) : (
        <Login />
      )}
    </>
  )
}

export default App

