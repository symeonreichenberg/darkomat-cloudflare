(() => {
  const page = window.DARKOMAT_PAGE;
  if (!page) return;

  const form = document.getElementById(`${page}-form`);
  const error = document.getElementById(`${page}-error`);
  if (!form || !error) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    if (!payload.email || !payload.password || (page === "register" && !payload.name)) {
      showError("required");
      return;
    }

    if (page === "register" && payload.password.length < 8) {
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
        showError(result.message || "Request failed.");
        return;
      }

      window.location.href = result.redirect || "/";
    } catch {
      showError("Something went wrong. Please try again.");
    }
  });

  function showError(message) {
    error.textContent = message;
    error.hidden = false;
  }
})();
