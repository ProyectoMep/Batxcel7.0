// Controla el cambio entre secciones del menú lateral.
document.querySelectorAll(".menu-item[data-vista]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".menu-item[data-vista]").forEach((b) => b.classList.remove("activo"));
    btn.classList.add("activo");

    document.querySelectorAll("main > section").forEach((s) => s.classList.add("oculto"));
    document.getElementById(btn.dataset.vista).classList.remove("oculto");

    if (btn.dataset.vista === "vista-reporte" && typeof cargarVistaReporte === "function") {
      cargarVistaReporte();
    }
  });
});