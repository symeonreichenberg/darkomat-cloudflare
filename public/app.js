(() => {
  const page = window.DARKOMAT_PAGE;
  if (!page) return;

  const form = document.getElementById(`${page}-form`);
  const error = document.getElementById(`${page}-error`);
  if (!form || !error) return;

  const messages = {
    en: {
      required: "Please fill in all required fields.",
      password_short: "Password must be at least 8 characters.",
      register_failed: "We could not create your account. Please check your details and try again.",
      verification_failed: "We could not send the verification email. Please try again later.",
      email_not_verified: "Please verify your email address before logging in.",
      login_failed: "The email or password is incorrect.",
      unexpected: "Something went wrong. Please try again."
    },
    cs: {
      required: "Vyplňte prosím všechna povinná pole.",
      password_short: "Heslo musí mít alespoň 8 znaků.",
      register_failed: "Účet se nepodařilo vytvořit. Zkontrolujte údaje a zkuste to znovu.",
      verification_failed: "Ověřovací e-mail se nepodařilo odeslat. Zkuste to později.",
      email_not_verified: "Před přihlášením prosím potvrďte svůj e-mail.",
      login_failed: "E-mail nebo heslo není správné.",
      unexpected: "Něco se pokazilo. Zkuste to prosím znovu."
    }
  };

  const language = document.documentElement.lang === "cs" ? "cs" : "en";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;

    const payload = Object.fromEntries(new FormData(form).entries());

    if (!payload.email || !payload.password || (page === "register" && !payload.name)) {
      showError("required");
      return;
    }

    if (payload.password.length < 8) {
      showError("password_short");
      return;
    }

    try {
      const response = await fetch(`/api/${page}`, {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (!response.ok || !result.ok) {
        showError(result.error || "unexpected");
        return;
      }

      if (page === "register") {
        window.location.href = "/login";
        return;
      }

      window.location.href = "/account";
    } catch {
      showError("unexpected");
    }
  });

  function showError(key) {
    error.textContent = messages[language][key] || messages[language].unexpected;
    error.hidden = false;
  }
})();
