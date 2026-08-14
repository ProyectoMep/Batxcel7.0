const selEntidad = document.getElementById("ppt-entidad");
const selFechaActual = document.getElementById("ppt-fecha-actual");
const selFechaAnterior = document.getElementById("ppt-fecha-anterior");
const inputNombre = document.getElementById("ppt-nombre");
const btnGenerarPpt = document.getElementById("btn-generar-ppt");
const pptEstado = document.getElementById("ppt-estado");
const pptHistorico = document.getElementById("ppt-historico");

let vistaPresentacionCargada = false;

const menuPresentacion = document.querySelector('.menu-item[data-vista="vista-presentacion"]');
if (menuPresentacion) {
  menuPresentacion.addEventListener("click", () => {
    if (!vistaPresentacionCargada) {
      vistaPresentacionCargada = true;
      cargarEntidadesPpt();
      cargarHistoricoPpt();
    }
  });
}

selEntidad.addEventListener("change", cargarFechasPpt);
btnGenerarPpt.addEventListener("click", generarPresentacion);

async function cargarEntidadesPpt() {
  const res = await fetch("/api/entidades");
  const entidades = await res.json();
  selEntidad.innerHTML = entidades.map((e) => `<option value="${escapeHtmlP(e.nombre)}">${escapeHtmlP(e.nombre)}</option>`).join("");
  if (entidades.length) cargarFechasPpt();
}

async function cargarFechasPpt() {
  const entidad = selEntidad.value;
  if (!entidad) return;
  const res = await fetch(`/api/presentacion/fechas/${entidad}`);
  const fechas = await res.json();

  selFechaActual.innerHTML = fechas.map((f) => `<option value="${f}">${f}</option>`).join("");
  selFechaAnterior.innerHTML = '<option value="">Automático</option>' +
    fechas.map((f) => `<option value="${f}">${f}</option>`).join("");
}

async function generarPresentacion() {
  const entidad = selEntidad.value;
  const fechaActual = selFechaActual.value;
  if (!entidad || !fechaActual) {
    pptEstado.textContent = "❌ Selecciona entidad y fecha";
    pptEstado.className = "ayuda error";
    return;
  }

  btnGenerarPpt.disabled = true;
  pptEstado.textContent = "⏳ Generando presentación...";
  pptEstado.className = "ayuda";

  const payload = {
    entidad,
    fecha_actual: fechaActual,
    fecha_anterior: selFechaAnterior.value || null,
    nombre: inputNombre.value.trim() || null,
  };

  try {
    const res = await fetch("/api/presentacion/generar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      pptEstado.textContent = "❌ " + (data.error || "No se pudo generar");
      pptEstado.className = "ayuda error";
    } else {
      const pdfTexto = data.pdf ? ` + PDF (${data.pdf})` : " (PDF no disponible, requiere PowerPoint instalado)";
      pptEstado.textContent = `✅ Generado: ${data.pptx}${pdfTexto}. Comparado contra ${data.fecha_anterior}.`;
      pptEstado.className = "ayuda ok";
      cargarHistoricoPpt();
    }
  } catch (err) {
    pptEstado.textContent = "❌ Error de conexión";
    pptEstado.className = "ayuda error";
  } finally {
    btnGenerarPpt.disabled = false;
  }
}

async function cargarHistoricoPpt() {
  const res = await fetch("/api/presentacion/historico");
  const historico = await res.json();

  const entidades = Object.keys(historico);
  if (!entidades.length) {
    pptHistorico.innerHTML = "<p class='ayuda'>No hay entidades configuradas.</p>";
    return;
  }

  pptHistorico.innerHTML = entidades.map((entidad) => {
    const items = historico[entidad];
    if (!items.length) {
      return `<h4>${escapeHtmlP(entidad)}</h4><p class="ayuda">Sin presentaciones generadas todavía.</p>`;
    }
    return `
      <h4>${escapeHtmlP(entidad)}</h4>
      <table class="tabla-metricas">
        <thead><tr><th>Fecha</th><th>Nombre</th><th>Archivos</th></tr></thead>
        <tbody>
          ${items.map((it) => `
            <tr>
              <td>${escapeHtmlP(it.fecha)}</td>
              <td>${escapeHtmlP(it.nombre)}</td>
              <td>
                <a class="btn-secundario btn-link" href="/api/presentacion/descargar/${encodeURIComponent(it.fecha)}/${encodeURIComponent(it.pptx)}?dl=1">Descargar PPTX</a>
                ${it.pdf ? `<a class="btn-secundario btn-link" href="/api/presentacion/descargar/${encodeURIComponent(it.fecha)}/${encodeURIComponent(it.pdf)}?dl=1">Descargar PDF</a>` : ""}
              </td>
            </tr>`).join("")}
        </tbody>
      </table>`;
  }).join("");
}

function escapeHtmlP(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}