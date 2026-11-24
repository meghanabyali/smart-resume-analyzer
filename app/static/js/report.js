// Printable report page (inline handlers are blocked by the Content-Security-Policy).
document.querySelectorAll(".js-print").forEach((b) => b.addEventListener("click", () => window.print()));
