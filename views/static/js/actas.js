const selActaEntidad = document.getElementById("acta-entidad");
const selActaPresentacion = document.getElementById("acta-presentacion");
const inputActaNumero = document.getElementById("acta-numero");
const inputActaFechaReunion = document.getElementById("acta-fecha-reunion");
const inputActaNombre = document.getElementById("acta-nombre");
const btnGenerarActa = document.getElementById("btn-generar-acta");
const btnImportarActa = document.getElementById("btn-importar-acta");
const importarEstado = document.getElementById("importar-estado");
const actaEstado = document.getElementById("acta-estado");
const actaHistorico = document.getElementById("acta-historico");

const listaAsistentes = document.getElementById("lista-asistentes");
const labelAsistenteForm = document.getElementById("label-asistente-form");
const inputNuevoAsistenteNombre = document.getElementById("nuevo-asistente-nombre");
const inputNuevoAsistenteCargo = document.getElementById("nuevo-asistente-cargo");
const selNuevoAsistenteEstado = document.getElementById("nuevo-asistente-estado");
const btnAgregarAsistente = document.getElementById("btn-agregar-asistente");
const btnCancelarEdicionAsistente = document.getElementById("btn-cancelar-edicion-asistente");

const listaObservaciones = document.getElementById("lista-observaciones");
const inputNuevaObservacionTexto = document.getElementById("nueva-observacion-texto");
const btnAgregarObservacion = document.getElementById("btn-agregar-observacion");

let vistaActasCargada = false;
let presentacionesCache = [];
let asistenteEditandoId = null;   // null = modo "agregar", número = modo "editar"

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
  cargarPresentacionesActa();
  cargarAsistentes();
  cargarObservaciones();
});
selActaPresentacion.addEventListener("change", aplicarPresentacionSeleccionada);
btnGenerarActa.addEventListener("click", generarActa);
btnImportarActa.addEventListener("click", importarDesdeActa);
btnAgregarAsistente.addEventListener("click", guardarAsistente);
btnCancelarEdicionAsistente.addEventListener("click", cancelarEdicionAsistente);
btnAgregarObservacion.addEventListener("click", agregarObservacion);

async function cargarEntidadesActa() {
  const res = await fetch("/api/entidades");
  const entidades = await res.json();
  selActaEntidad.innerHTML = entidades.map((e) => `<option value="${escapeHtmlA(e.nombre)}">${escapeHtmlA(e.nombre)}</option>`).join("");
  if (entidades.length) {
    cargarPresentacionesActa();
    cargarAsistentes();
    cargarObservaciones();
  }
}

// ─────────────── PRESENTACIÓN DE ORIGEN ───────────────

async function cargarPresentacionesActa() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;
  const res = await fetch(`/api/acta/presentaciones/${entidad}`);
  presentacionesCache = await res.json();

  if (!presentacionesCache.length) {
    selActaPresentacion.innerHTML = "<option value=''>Sin presentaciones generadas</option>";
    return;
  }

  selActaPresentacion.innerHTML = presentacionesCache
    .map((p, i) => `<option value="${i}">${escapeHtmlA(p.nombre)}</option>`).join("");
  aplicarPresentacionSeleccionada();
}

function aplicarPresentacionSeleccionada() {
  const idx = parseInt(selActaPresentacion.value, 10);
  const p = presentacionesCache[idx];
  if (!p) return;
  if (!inputActaFechaReunion.value) {
    inputActaFechaReunion.value = p.fecha_actual;
  }
}

// ─────────────── ASISTENTES (con edición) ───────────────

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
      <span>
        <button type="button" class="btn-secundario" onclick='editarAsistente(${JSON.stringify(a)})'>Editar</button>
        <button type="button" class="btn-secundario" onclick="eliminarAsistente(${a.id})">Quitar</button>
      </span>
    </div>`).join("");
}

function editarAsistente(a) {
  asistenteEditandoId = a.id;
  inputNuevoAsistenteNombre.value = a.nombre;
  inputNuevoAsistenteCargo.value = a.cargo;
  selNuevoAsistenteEstado.value = a.estado || "Asistió";
  labelAsistenteForm.textContent = "Editando asistente:";
  btnAgregarAsistente.textContent = "Guardar cambios";
  btnCancelarEdicionAsistente.classList.remove("oculto");
  inputNuevoAsistenteNombre.focus();
}

function cancelarEdicionAsistente() {
  asistenteEditandoId = null;
  inputNuevoAsistenteNombre.value = "";
  inputNuevoAsistenteCargo.value = "";
  selNuevoAsistenteEstado.value = "Asistió";
  labelAsistenteForm.textContent = "Nombre";
  btnAgregarAsistente.textContent = "+ Agregar";
  btnCancelarEdicionAsistente.classList.add("oculto");
}

async function guardarAsistente() {
  const entidad = selActaEntidad.value;
  const nombre = inputNuevoAsistenteNombre.value.trim();
  if (!entidad || !nombre) return;

  const payload = {
    nombre, cargo: inputNuevoAsistenteCargo.value.trim(),
    estado: selNuevoAsistenteEstado.value,
  };

  const url = asistenteEditandoId
    ? `/api/acta/asistentes/${entidad}/${asistenteEditandoId}`
    : `/api/acta/asistentes/${entidad}`;
  const metodo = asistenteEditandoId ? "PUT" : "POST";

  const res = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) return alert("No se pudo guardar el asistente");

  cancelarEdicionAsistente();
  cargarAsistentes();
}

async function eliminarAsistente(id) {
  const entidad = selActaEntidad.value;
  await fetch(`/api/acta/asistentes/${entidad}/${id}`, { method: "DELETE" });
  if (asistenteEditandoId === id) cancelarEdicionAsistente();
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

// ─────────────── IMPORTAR (reemplaza, nunca duplica) ───────────────

async function importarDesdeActa() {
  const entidad = selActaEntidad.value;
  if (!entidad) return;

  if (!confirm("Esto va a reemplazar la lista actual de asistentes y observaciones "
              + "con la de la última acta generada. ¿Continuar?")) return;

  importarEstado.textContent = "⏳ Importando...";
  importarEstado.className = "ayuda";

  const res = await fetch(`/api/acta/importar/${entidad}`, { method: "POST" });
  const data = await res.json();

  if (!res.ok || !data.ok) {
    importarEstado.textContent = "❌ " + (data.error || "No se encontró ninguna acta anterior");
    importarEstado.className = "ayuda error";
    return;
  }

  importarEstado.textContent = `✅ Importado de "${data.archivo}": ${data.asistentes_importados} asistente(s), ${data.observaciones_importadas} observación(es).`;
  importarEstado.className = "ayuda ok";
  cancelarEdicionAsistente();
  cargarAsistentes();
  cargarObservaciones();
}

// ─────────────── GENERAR ───────────────

async function generarActa() {
  const idx = parseInt(selActaPresentacion.value, 10);
  const p = presentacionesCache[idx];

  if (!p) {
    actaEstado.textContent = "❌ Selecciona una presentación de origen";
    actaEstado.className = "ayuda error";
    return;
  }

  const payload = {
    entidad: selActaEntidad.value,
    fecha_actual: p.fecha_actual,
    fecha_anterior: p.fecha_anterior,
    numero: inputActaNumero.value.trim(),
    fecha_reunion: inputActaFechaReunion.value,
    nombre: inputActaNombre.value.trim() || null,
  };

  if (!payload.entidad || !payload.numero || !payload.fecha_reunion) {
    actaEstado.textContent = "❌ Completa entidad, número de acta y fecha de reunión";
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