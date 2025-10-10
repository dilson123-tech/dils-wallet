export default function LoginPage() {
  const handleLogin = () => {
    localStorage.setItem("auth_token", "demo");
    window.location.href = "/admin/users";
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-950 text-white">
      <h1 className="text-3xl font-bold text-yellow-500 mb-2">Aurea Gold Admin</h1>
      <p className="mb-6">Interface de login funcionando ✅</p>
      <button
        onClick={handleLogin}
        className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold py-2 px-6 rounded shadow-lg transition"
      >
        Entrar
      </button>
    </div>
  );
}
