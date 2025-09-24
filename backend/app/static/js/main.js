(function(){
  const $ = (sel) => document.querySelector(sel);
  const out = $("#out");
  const loginForm = $("#loginForm");
  const loginStatus = $("#loginStatus");
  const btnSaldo = $("#btnSaldo");
  const btnEntrar = loginForm.querySelector('button[type="submit"]');
  const emailInput = $("#email");
  const passInput = $("#password");

  function setStatus(msg, ok=false){
    loginStatus.textContent = (ok ? "✅ " : "❌ ") + msg;
  }

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    btnEntrar.disabled = true;
    btnEntrar.textContent = "Entrando...";
    loginStatus.textContent = "Autenticando...";

    try {
      const email = emailInput.value.trim();
      const password = passInput.value;
      await AUTH.login(email, password);
      setStatus("Login ok (access token salvo).", true);

      // limpar campos após sucesso
      emailInput.value = "";
      passInput.value = "";
    } catch (err) {
      // mensagem clara + limpar só a senha
      passInput.value = "";
      setStatus(err?.message || "Erro de login");
    } finally {
      btnEntrar.disabled = false;
      btnEntrar.textContent = "Entrar";
    }
  });

  btnSaldo.addEventListener("click", async () => {
    out.textContent = "Consultando saldo...";
    try {
      const data = await API.apiGet("/transactions/balance");
      out.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      out.textContent = "Erro: " + (err?.message || "Falha na requisição");
    }
  });
})();
