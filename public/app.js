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
      login_failed: "The email or password is incorrect.",
      unexpected: "Something went wrong. Please try again."
    },
    cs: {
      required: "Vyplňte prosím všechna povinná pole.",
      password_short: "Heslo musí mít alespoň 8 znaků.",
      register_failed: "Účet se nepodařilo vytvořit. Zkontrolujte údaje a zkuste to znovu.",
      login_failed: "E-mail nebo heslo není správné.",
      unexpected: "Něco se pokazilo. Zkuste to prosím znovu."
    }
  };

  const language = document.documentElement.lang === "cs" ? "cs" : "en";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

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

      // Authentication state will be added with the session layer.
      // For now, successful registration/login has a clear functional response.
      window.location.href = "/";
    } catch {
      showError("unexpected");
    }
  });

  function showError(key) {
    error.textContent = messages[language][key] || messages[language].unexpected;
    error.hidden = false;
  }
})();
