(() => {
  const page = window.DARKOMAT_PAGE;
  if (!page) return;
  const form = document.getElementById(`${page}-form`);
  const error = document.getElementById(`${page}-error`);
  if (!form || !error) return;
  const messages = window.DARKOMAT_MESSAGES || {};
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      const response = await fetch(`/api/${page}`, {
        method: "POST",
        headers: {"content-type":"application/json"},
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        error.textContent = messages[result.error] || messages.unexpected;
        error.hidden = false;
        return;
      }
      window.location.href = page === "login" ? "/app" : "/app";
    } catch {
      error.textContent = messages.unexpected;
      error.hidden = false;
    }
  });
})();
