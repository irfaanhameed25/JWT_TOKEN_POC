import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div style={{ padding: '30px', fontFamily: 'sans-serif', maxWidth: '600px', margin: 'auto' }}>
      <h2>FastAPI + React JWT Auth POC</h2>

      {/* Login Form */}
      <form onSubmit={handleLogin} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '5px' }}>
        <h3>Login</h3>
        <div style={{ marginBottom: '10px' }}>
          <label>Username: </label>
          <input 
            type="text" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>Password: </label>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
          />
        </div>
        <button type="submit">Login</button>
      </form>

      {/* Action Buttons for Routes */}
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button onClick={() => callProtectedApi('/dashboard')}>Test /dashboard (All Users)</button>
        <button onClick={() => callProtectedApi('/manager/reports')}>Test /manager/reports (Manager Only)</button>
        <button onClick={() => callProtectedApi('/admin/system-logs')}>Test /admin/system-logs (Admin Only)</button>
      </div>

      {/* Output Console Box */}
      <div style={{ marginTop: '20px' }}>
        <h3>Output:</h3>
        <pre style={{ background: '#f4f4f4', padding: '15px', borderRadius: '5px', minHeight: '80px' }}>
          {output}
        </pre>
      </div>
    </div>
  );
}

export default App;