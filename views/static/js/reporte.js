const btnGenerar = document.getElementById("btn-generar-reporte");
const gridEstadoInput = document.getElementById("grid-estado-input");
const estadoGeneracion = document.getElementById("estado-generacion");
const arbolOutput = document.getElementById("arbol-output");

const modalPreview = document.getElementById("modal-preview");
const previewTitulo = document.getElementById("preview-titulo");
const previewTabs = document.getElementById("preview-tabs");
const previewContenido = document.getElementById("preview-contenido");

const modalInstrucciones = document.getElementById("modal-instrucciones");
const instruccionesTitulo = document.getElementById("instrucciones-titulo");
const instruccionesTexto = document.getElementById("instrucciones-texto");
const instruccionesImagen = document.getElementById("instrucciones-imagen");

btnGenerar.addEventListener("click", generarReporte);
document.getElementById("btn-cerrar-preview").addEventListener("click", () => {
  modalPreview.classList.add("oculto");
});
document.getElementById("btn-cerrar-instrucciones").addEventListener("click", () => {
  modalInstrucciones.classList.add("oculto");
});

let intervaloEstado = null;
let metricasEstadoActual = [];

cargarVistaReporte();

function cargarVistaReporte() {
  cargarEstadoInput();
  cargarArbolOutput();
}

async function cargarEstadoInput() {
  gridEstadoInput.innerHTML = "<p class='ayuda-oscura'>Cargando estado de archivos...</p>";

  let data;
  try {
    const res = await fetch("/api/reporte/estado-input");
    if (!res.ok) {
      const texto = await res.text();
      throw new Error(`El servidor respondió ${res.status}: ${texto.slice(0, 200)}`);
    }
    data = await res.json();
  } catch (err) {
    gridEstadoInput.innerHTML = `<p class='ayuda-oscura error-oscuro'>❌ Error cargando estado: ${escapeHtmlR(err.message)}</p>`;
    btnGenerar.disabled = true;
    console.error("Error en cargarEstadoInput:", err);
    return;
  }

  metricasEstadoActual = data.metricas || [];
  const faltantes = data.faltantes || [];

  if (!metricasEstadoActual.length) {
    gridEstadoInput.innerHTML = "<p class='ayuda-oscura'>No hay métricas obligatorias configuradas todavía.</p>";
    btnGenerar.disabled = true;
    return;
  }

  gridEstadoInput.innerHTML = metricasEstadoActual.map((m, i) => `
    <div class="fila-estado">
      <span class="icono-estado">${m.encontrado ? "✅" : "❌"}</span>
      <span class="nombre-estado">${escapeHtmlR(m.nombre)}</span>
      <button type="button" class="btn-ojo" onclick="abrirInstrucciones(${i})" title="Ver instrucciones">👁</button>
    </div>`).join("");

  if (faltantes.length) {
    estadoGeneracion.textContent = "Falta: " + faltantes.join(", ");
    estadoGeneracion.className = "ayuda-oscura error-oscuro";
    btnGenerar.disabled = true;
  } else {
    estadoGeneracion.textContent = "";
    btnGenerar.disabled = false;
  }
}

function abrirInstrucciones(indice) {
  const m = metricasEstadoActual[indice];
  if (!m) return;

  instruccionesTitulo.textContent = m.nombre;
  instruccionesTexto.textContent = m.instrucciones_descarga && m.instrucciones_descarga.trim()
    ? m.instrucciones_descarga
    : "Todavía no se han registrado instrucciones para esta métrica. Edítala en la sección Métricas para agregarlas.";

  if (m.imagen_instructivo) {
    instruccionesImagen.src = `/static/${m.imagen_instructivo}`;
    instruccionesImagen.classList.remove("oculto");
  } else {
    instruccionesImagen.classList.add("oculto");
  }

  modalInstrucciones.classList.remove("oculto");
}

async function generarReporte() {
  btnGenerar.disabled = true;
  estadoGeneracion.textContent = "Iniciando...";
  estadoGeneracion.className = "ayuda-oscura";

  const res = await fetch("/api/reporte/generar", { method: "POST" });
  const data = await res.json();

  if (!res.ok || !data.ok) {
    estadoGeneracion.textContent = "❌ " + (data.error || "No se pudo iniciar");
    estadoGeneracion.className = "ayuda-oscura error-oscuro";
    btnGenerar.disabled = false;
    return;
  }

  estadoGeneracion.textContent = "⏳ Generando reporte, esto puede tardar unos minutos...";
  estadoGeneracion.className = "ayuda-oscura";
  intervaloEstado = setInterval(consultarEstadoProceso, 2000);
}

async function consultarEstadoProceso() {
  const res = await fetch("/api/reporte/estado-proceso");
  const data = await res.json();

  if (data.corriendo) return;

  clearInterval(intervaloEstado);
  btnGenerar.disabled = false;

  if (data.resultado && data.resultado.ok) {
    estadoGeneracion.textContent = `✅ Reporte generado (${data.resultado.fecha}): ${data.resultado.archivos.join(", ")}`;
    estadoGeneracion.className = "ayuda-oscura ok-oscuro";
    cargarArbolOutput();
  } else {
    const error = data.resultado ? data.resultado.error : "Error desconocido";
    estadoGeneracion.textContent = "❌ " + error;
    estadoGeneracion.className = "ayuda-oscura error-oscuro";
  }
}

async function cargarArbolOutput() {
  const res = await fetch("/api/reporte/arbol-output");
  const arbol = await res.json();

  if (!arbol.length) {
    arbolOutput.innerHTML = "<p class='ayuda-oscura'>Todavía no hay reportes generados.</p>";
    return;
  }

  arbolOutput.innerHTML = arbol.map((carpeta, i) => `
    <div class="carpeta-fecha-oscura">
      <button type="button" class="acordeon-header" onclick="toggleAcordeon(${i})">
        <span>📅 ${escapeHtmlR(carpeta.fecha)}</span>
        <span class="acordeon-flecha" id="flecha-${i}">▸</span>
      </button>
      <ul class="lista-archivos-oscura oculto" id="lista-${i}">
        ${carpeta.archivos.map((archivo) => `
          <li>
            <span>${escapeHtmlR(archivo)}</span>
            <span>
              <button class="btn-secundario" onclick="abrirPreview('${carpeta.fecha}', '${escapeAttr(archivo)}')">Ver</button>
              <a class="btn-secundario btn-link" href="/api/reporte/descargar/${encodeURIComponent(carpeta.fecha)}/${encodeURIComponent(archivo)}?dl=1">Descargar</a>
            </span>
          </li>`).join("")}
      </ul>
    </div>`).join("");
}

function toggleAcordeon(indice) {
  const lista = document.getElementById(`lista-${indice}`);
  const flecha = document.getElementById(`flecha-${indice}`);
  const abierto = !lista.classList.contains("oculto");
  lista.classList.toggle("oculto", abierto);
  flecha.textContent = abierto ? "▸" : "▾";
}

async function abrirPreview(fecha, nombre) {
  previewTitulo.textContent = `${nombre} (${fecha})`;
  previewContenido.innerHTML = "Cargando...";
  previewTabs.innerHTML = "";
  modalPreview.classList.remove("oculto");

  const res = await fetch(`/api/reporte/preview/${encodeURIComponent(fecha)}/${encodeURIComponent(nombre)}`);
  const data = await res.json();

  if (!res.ok || !data.ok) {
    previewContenido.innerHTML = `<p class="ayuda error">${escapeHtmlR(data.error || "No se pudo cargar la vista previa")}</p>`;
    return;
  }

  previewTabs.innerHTML = data.hojas.map((h, i) => `
    <button type="button" class="tab-btn ${i === 0 ? "activo" : ""}" onclick="mostrarHojaPreview(${i})">
      ${escapeHtmlR(h.nombre)} (${h.filas})
    </button>`).join("");

  window._hojasPreview = data.hojas;
  mostrarHojaPreview(0);
}

function mostrarHojaPreview(indice) {
  document.querySelectorAll(".tab-btn").forEach((b, i) => b.classList.toggle("activo", i === indice));
  previewContenido.innerHTML = window._hojasPreview[indice].html;
}

function escapeHtmlR(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function escapeAttr(str) {
  return String(str).replace(/'/g, "\\'");
}