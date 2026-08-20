const selProsperaFecha = document.getElementById("prospera-fecha");
const inputProsperaArchivo = document.getElementById("prospera-archivo");
const inputProsperaNombre = document.getElementById("prospera-nombre");
const btnGenerarProspera = document.getElementById("btn-generar-prospera");
const prosperaEstado = document.getElementById("prospera-estado");
const prosperaHistorico = document.getElementById("prospera-historico");

let vistaProsperaCargada = false;

const menuProspera = document.querySelector('.menu-item[data-vista="vista-prospera"]');
if (menuProspera) {
  menuProspera.addEventListener("click", () => {
    if (!vistaProsperaCargada) {
      vistaProsperaCargada = true;
      cargarFechasProspera();
      cargarHistoricoProspera();
    }
  });
}

btnGenerarProspera.addEventListener("click", generarProspera);

async function cargarFechasProspera() {
  const res = await fetch("/api/prospera/fechas");
  const fechas = await res.json();
  selProsperaFecha.innerHTML = fechas.map((f) => `<option value="${f}">${f}</option>`).join("");
}

async function generarProspera() {
  const fecha = selProsperaFecha.value;
  const archivo = inputProsperaArchivo.files[0];

  if (!fecha) {
    prosperaEstado.textContent = "❌ Selecciona la fecha del resumen";
    prosperaEstado.className = "ayuda error";
    return;
  }
  if (!archivo) {
    prosperaEstado.textContent = "❌ Debes cargar el archivo Cloud_Authentication (.xlsx)";
    prosperaEstado.className = "ayuda error";
    return;
  }

  btnGenerarProspera.disabled = true;
  prosperaEstado.textContent = "⏳ Generando...";
  prosperaEstado.className = "ayuda";

  const fd = new FormData();
  fd.append("fecha_resumen", fecha);
  fd.append("nombre", inputProsperaNombre.value.trim());
  fd.append("archivo", archivo);

  try {
    const res = await fetch("/api/prospera/generar", { method: "POST", body: fd });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      prosperaEstado.textContent = "❌ " + (data.error || "No se pudo generar");
      prosperaEstado.className = "ayuda error";
    } else {
      prosperaEstado.textContent = `✅ Generado: ${data.archivo} — ${data.sin_metodos} sin métodos, ` +
        `${data.en_resumen} coinciden con el resumen, ${data.finales} final(es) (Customer Sales & Support).`;
      prosperaEstado.className = "ayuda ok";
      cargarHistoricoProspera();
    }
  } catch (err) {
    prosperaEstado.textContent = "❌ Error de conexión";
    prosperaEstado.className = "ayuda error";
  } finally {
    btnGenerarProspera.disabled = false;
  }
}

async function cargarHistoricoProspera() {
  const res = await fetch("/api/prospera/historico");
  const items = await res.json();

  if (!items.length) {
    prosperaHistorico.innerHTML = "<p class='ayuda'>Sin archivos Prospera generados todavía.</p>";
    return;
  }

  prosperaHistorico.innerHTML = `
    <table class="tabla-metricas">
      <thead><tr><th>Fecha</th><th>Nombre</th><th>Archivo</th></tr></thead>
      <tbody>
        ${items.map((it) => `
          <tr>
            <td>${escapeHtmlPr(it.fecha)}</td>
            <td>${escapeHtmlPr(it.nombre)}</td>
            <td>
              <a class="btn-secundario btn-link" href="/api/prospera/descargar/${encodeURIComponent(it.fecha)}/${encodeURIComponent(it.xlsx)}?dl=1">Descargar</a>
            </td>
          </tr>`).join("")}
      </tbody>
    </table>`;
}

function escapeHtmlPr(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}