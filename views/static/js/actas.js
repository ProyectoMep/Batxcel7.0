const selActaEntidad = document.getElementById("acta-entidad");
const selActaFechaActual = document.getElementById("acta-fecha-actual");
const selActaFechaAnterior = document.getElementById("acta-fecha-anterior");
const inputActaNumero = document.getElementById("acta-numero");
const inputActaFechaReunion = document.getElementById("acta-fecha-reunion");
const inputActaHoraInicio = document.getElementById("acta-hora-inicio");
const inputActaHoraFin = document.getElementById("acta-hora-fin");
const inputActaNombre = document.getElementById("acta-nombre");
const btnGenerarActa = document.getElementById("btn-generar-acta");
const btnImportarActa = document.getElementById("btn-importar-acta");
const importarEstado = document.getElementById("importar-estado");
const actaEstado = document.getElementById("acta-estado");
const actaHistorico = document.getElementById("acta-historico");

const listaAsistentes = document.getElementById("lista-asistentes");
const inputNuevoAsistenteNombre = document.getElementById("nuevo-asistente-nombre");
const inputNuevoAsistenteCargo = document.getElementById("nuevo-asistente-cargo");
const btnAgregarAsistente = document.getElementById("btn-agregar-asistente");

const listaObservaciones = document.getElementById("lista-observaciones");
const inputNuevaObservacionTexto = document.getElementById("nueva-observacion-texto");
const btnAgregarObservacion = document.getElementById("btn-agregar-observacion");

let vistaActasCargada = false;

const menuActas = document.querySelector('.menu-item[data-vista="vista-actas"]');
if (menuActas) {
  menuActas.addEventListener("click", () => {
    if (!vistaActasCargada) {
      vistaActasCargada = true;
      cargarEntidadesActa();
      cargarHistoricoActa();
    }
  });
}

selActaEntidad.addEventListener("change", () => {
  cargarFechasActa();
  cargarAsistentes();
  cargarObservaciones();
});
btnGenerarActa.addEventListener("click", generarActa);
btnImportarActa.addEventListener("click", importarDesdeActa);
btnAgregarAsistente.addEventListener("click", agregarAsistente);
btnAgregarObservacion.addEventListener("click", agregarObservacion);

async function importarDesdeActa() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;

  importarEstado.textContent = "⏳ Importando...";
  importarEstado.className = "ayuda";

  const res = await fetch(`/api/acta/importar/${entidad}`, { method: "POST" });
  const data = await res.json();

  if (!res.ok || !data.ok) {
    importarEstado.textContent = "❌ " + (data.error || "No se encontró ninguna acta anterior");
    importarEstado.className = "ayuda error";
    return;
  }

  const omitidos = (data.asistentes_omitidos || 0) + (data.observaciones_omitidas || 0);
  const textoOmitidos = omitidos > 0 ? ` (${omitidos} ya existían, se omitieron)` : "";
  importarEstado.textContent = `✅ Importado de "${data.archivo}": ${data.asistentes_importados} asistente(s) nuevo(s), ${data.observaciones_importadas} observación(es) nueva(s)${textoOmitidos}.`;
  importarEstado.className = "ayuda ok";
  cargarAsistentes();
  cargarObservaciones();
}

async function cargarEntidadesActa() {
  const res = await fetch("/api/entidades");
  const entidades = await res.json();
  selActaEntidad.innerHTML = entidades.map((e) => `<option value="${escapeHtmlA(e.nombre)}">${escapeHtmlA(e.nombre)}</option>`).join("");
  if (entidades.length) {
    cargarFechasActa();
    cargarAsistentes();
    cargarObservaciones();
  }
}

async function cargarFechasActa() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;
  const res = await fetch(`/api/acta/fechas/${entidad}`);
  const fechas = await res.json();
  const opciones = fechas.map((f) => `<option value="${f}">${f}</option>`).join("");
  selActaFechaActual.innerHTML = opciones;
  selActaFechaAnterior.innerHTML = opciones;
  if (fechas.length > 1) selActaFechaAnterior.value = fechas[1];
}

// ─────────────── ASISTENTES ───────────────

async function cargarAsistentes() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;
  const res = await fetch(`/api/acta/asistentes/${entidad}`);
  const asistentes = await res.json();

  if (!asistentes.length) {
    listaAsistentes.innerHTML = "<p class='ayuda'>Todavía no hay asistentes guardados.</p>";
    return;
  }

  listaAsistentes.innerHTML = asistentes.map((a) => `
    <div class="fila-item-simple">
      <span>${escapeHtmlA(a.nombre)}${a.cargo ? " — " + escapeHtmlA(a.cargo) : ""} <em>(${escapeHtmlA(a.estado || "Asistió")})</em></span>
      <button type="button" class="btn-secundario" onclick="eliminarAsistente(${a.id})">Quitar</button>
    </div>`).join("");
}

async function agregarAsistente() {
  const entidad = selActaEntidad.value;
  const nombre = inputNuevoAsistenteNombre.value.trim();
  if (!entidad || !nombre) return;

  const res = await fetch(`/api/acta/asistentes/${entidad}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre, cargo: inputNuevoAsistenteCargo.value.trim() }),
  });
  if (!res.ok) return alert("No se pudo agregar el asistente");

  inputNuevoAsistenteNombre.value = "";
  inputNuevoAsistenteCargo.value = "";
  cargarAsistentes();
}

async function eliminarAsistente(id) {
  const entidad = selActaEntidad.value;
  await fetch(`/api/acta/asistentes/${entidad}/${id}`, { method: "DELETE" });
  cargarAsistentes();
}

// ─────────────── OBSERVACIONES ───────────────

async function cargarObservaciones() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;
  const res = await fetch(`/api/acta/observaciones/${entidad}`);
  const observaciones = await res.json();

  if (!observaciones.length) {
    listaObservaciones.innerHTML = "<p class='ayuda'>Todavía no hay observaciones guardadas.</p>";
    return;
  }

  listaObservaciones.innerHTML = observaciones.map((o) => `
    <div class="fila-item-simple">
      <span>${escapeHtmlA(o.texto)}</span>
      <button type="button" class="btn-secundario" onclick="eliminarObservacion(${o.id})">Quitar</button>
    </div>`).join("");
}

async function agregarObservacion() {
  const entidad = selActaEntidad.value;
  const texto = inputNuevaObservacionTexto.value.trim();
  if (!entidad || !texto) return;

  const res = await fetch(`/api/acta/observaciones/${entidad}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  if (!res.ok) return alert("No se pudo agregar la observación");

  inputNuevaObservacionTexto.value = "";
  cargarObservaciones();
}

async function eliminarObservacion(id) {
  const entidad = selActaEntidad.value;
  await fetch(`/api/acta/observaciones/${entidad}/${id}`, { method: "DELETE" });
  cargarObservaciones();
}

// ─────────────── GENERAR ───────────────

async function generarActa() {
  const payload = {
    entidad: selActaEntidad.value,
    fecha_actual: selActaFechaActual.value,
    fecha_anterior: selActaFechaAnterior.value,
    numero: inputActaNumero.value.trim(),
    fecha_reunion: inputActaFechaReunion.value,
    hora_inicio: inputActaHoraInicio.value.trim(),
    hora_fin: inputActaHoraFin.value.trim(),
    nombre: inputActaNombre.value.trim() || null,
  };

  if (!payload.entidad || !payload.fecha_actual || !payload.fecha_anterior ||
      !payload.numero || !payload.fecha_reunion) {
    actaEstado.textContent = "❌ Completa entidad, fechas, número y fecha de reunión";
    actaEstado.className = "ayuda error";
    return;
  }

  btnGenerarActa.disabled = true;
  actaEstado.textContent = "⏳ Generando acta...";
  actaEstado.className = "ayuda";

  try {
    const res = await fetch("/api/acta/generar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      actaEstado.textContent = "❌ " + (data.error || "No se pudo generar");
      actaEstado.className = "ayuda error";
    } else {
      actaEstado.textContent = `✅ Generada: ${data.archivo} (${data.metricas} métricas, ${data.asistentes} asistentes, ${data.observaciones} observaciones)`;
      actaEstado.className = "ayuda ok";
      cargarHistoricoActa();
    }
  } catch (err) {
    actaEstado.textContent = "❌ Error de conexión";
    actaEstado.className = "ayuda error";
  } finally {
    btnGenerarActa.disabled = false;
  }
}

// ─────────────── HISTÓRICO ───────────────

async function cargarHistoricoActa() {
  const res = await fetch("/api/acta/historico");
  const historico = await res.json();

  const entidades = Object.keys(historico);
  if (!entidades.length) {
    actaHistorico.innerHTML = "<p class='ayuda'>No hay entidades configuradas.</p>";
    return;
  }

  actaHistorico.innerHTML = entidades.map((entidad) => {
    const items = historico[entidad];
    if (!items.length) {
      return `<h4>${escapeHtmlA(entidad)}</h4><p class="ayuda">Sin actas generadas todavía.</p>`;
    }
    return `
      <h4>${escapeHtmlA(entidad)}</h4>
      <table class="tabla-metricas">
        <thead><tr><th>Fecha</th><th>Nombre</th><th>Archivo</th></tr></thead>
        <tbody>
          ${items.map((it) => `
            <tr>
              <td>${escapeHtmlA(it.fecha)}</td>
              <td>${escapeHtmlA(it.nombre)}</td>
              <td>
                <a class="btn-secundario btn-link" href="/api/acta/descargar/${encodeURIComponent(it.fecha)}/${encodeURIComponent(it.docx)}?dl=1">Descargar</a>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>`;
  }).join("");
}

function escapeHtmlA(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}