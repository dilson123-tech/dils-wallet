export default function Header() {
  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    window.location.href = "/login";
  };

  return (
    <header className="gold-gradient gold-shine fixed top-0 left-0 w-full text-black shadow-lg border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto flex justify-between items-center px-6 py-3">
        <h1 className="text-xl font-extrabold tracking-wide">
          <span className="text-gray-900">Aurea</span> Gold <span className="font-light">Admin</span>
        </h1>
        <button onClick={handleLogout} className="gold-button gold-shine">Sair</button>
      </div>
    </header>
  );
}
