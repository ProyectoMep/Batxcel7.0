const OPERADORES = [
  { valor: "igual", texto: "Igual a" },
  { valor: "distinto", texto: "Distinto de" },
  { valor: "contiene", texto: "Contiene" },
  { valor: "no_contiene", texto: "No contiene" },
  { valor: "vacio", texto: "Está vacío" },
  { valor: "no_vacio", texto: "No está vacío" },
];

let columnasDetectadas = [];
let contadorCruce = 0;

const tbody = document.getElementById("tbody-metricas");
const modal = document.getElementById("modal-metrica");
const form = document.getElementById("form-metrica");
const condicionesContainer = document.getElementById("condiciones-container");
const limpiezaContainer = document.getElementById("limpieza-container");
const enriquecimientosContainer = document.getElementById("enriquecimientos-container");
const separacionContainer = document.getElementById("separacion-container");
const inputArchivo = document.getElementById("metrica-archivo-subida");
const estadoAnalisis = document.getElementById("estado-analisis");
const datalistColumnas = document.getElementById("datalist-columnas");

const inputImagen = document.getElementById("metrica-imagen");
const estadoImagen = document.getElementById("estado-imagen");
const previewImagenMetrica = document.getElementById("preview-imagen-metrica");
const inputImagenRuta = document.getElementById("metrica-imagen-ruta");

const cumplimientoAplica = document.getElementById("cumplimiento-aplica");
const cumplimientoDetalle = document.getElementById("cumplimiento-detalle");
const favorContainer = document.getElementById("cumplimiento-favor-container");
const totalModo = document.getElementById("cumplimiento-total-modo");
const totalFijoInput = document.getElementById("cumplimiento-total-fijo");
const totalContainer = document.getElementById("cumplimiento-total-container");
const btnAgregarTotal = document.getElementById("btn-agregar-total");
const excluirContainer = document.getElementById("cumplimiento-excluir-container");

document.getElementById("btn-nueva-metrica").addEventListener("click", () => abrirModal());
document.getElementById("btn-cancelar").addEventListener("click", cerrarModal);
document.getElementById("btn-agregar-condicion").addEventListener("click", () =>
  crearFilaCondicion(condicionesContainer, "datalist-columnas"));
document.getElementById("btn-agregar-limpieza").addEventListener("click", () =>
  crearFilaCondicion(limpiezaContainer, "datalist-columnas"));
document.getElementById("btn-agregar-cruce").addEventListener("click", () => agregarCruce());
document.getElementById("btn-agregar-separacion").addEventListener("click", () => agregarColumnaSeparacion());
document.getElementById("btn-agregar-favor").addEventListener("click", () =>
  crearFilaCondicion(favorContainer, "datalist-columnas"));
document.getElementById("btn-agregar-total").addEventListener("click", () =>
  crearFilaCondicion(totalContainer, "datalist-columnas"));
document.getElementById("btn-agregar-excluir").addEventListener("click", () =>
  crearFilaCondicion(excluirContainer, "datalist-columnas"));

cumplimientoAplica.addEventListener("change", () => {
  cumplimientoDetalle.classList.toggle("oculto", !cumplimientoAplica.checked);
});

totalModo.addEventListener("change", () => {
  const modo = totalModo.value;
  totalFijoInput.classList.toggle("oculto", modo !== "fijo");
  totalContainer.classList.toggle("oculto", modo !== "condicion");
  btnAgregarTotal.classList.toggle("oculto", modo !== "condicion");
});

form.addEventListener("submit", guardarMetrica);
inputArchivo.addEventListener("change", analizarArchivoSubido);
inputImagen.addEventListener("change", subirImagenMetrica);

cargarMetricas();

// ─────────────── LISTADO ───────────────

async function cargarMetricas() {
  const res = await fetch("/api/metricas");
  const metricas = await res.json();
  tbody.innerHTML = "";
  metricas.forEach((m) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(m.nombre)}${m.incluir_en_reporte ? "" : ' <span class="badge-no">solo cumplimiento</span>'}</td>
      <td>${escapeHtml(m.categoria || "-")}</td>
      <td>${m.obligatoria ? '<span class="badge-si">Obligatoria</span>' : '<span class="badge-no">Opcional</span>'}</td>
      <td>${escapeHtml(m.archivo_patron)}</td>
      <td>${contarCondiciones(m.criterios_incumplimiento)}</td>
      <td>${(m.enriquecimientos || []).length}</td>
      <td>${m.cumplimiento && m.cumplimiento.aplica ? '<span class="badge-si">Sí</span>' : '<span class="badge-no">No</span>'}</td>
      <td class="celda-acciones">
        <button class="btn-secundario btn-accion" onclick="editarMetrica(${m.id})">Editar</button>
        <button class="btn-secundario btn-accion" onclick="verBanderas(${m.id})">🏳️ Banderas</button>
        <button class="btn-secundario btn-accion" onclick="eliminarMetrica(${m.id})">Eliminar</button>
      </td>`;
    tbody.appendChild(tr);
  });
}

function contarCondiciones(grupos) {
  return (grupos || []).reduce((acc, grupo) => acc + grupo.length, 0);
}

// ─────────────── ANÁLISIS DE ARCHIVO (principal) ───────────────

async function analizarArchivoSubido() {
  const archivo = inputArchivo.files[0];
  if (!archivo) return;
  const resultado = await analizarArchivo(archivo, estadoAnalisis);
  if (!resultado) return;

  columnasDetectadas = resultado.columnas;
  poblarDatalist(datalistColumnas, columnasDetectadas);

  const campoPatron = document.getElementById("metrica-archivo-patron");
  if (!campoPatron.value.trim()) campoPatron.value = resultado.patron_sugerido;
}

async function analizarArchivo(archivo, elementoEstado) {
  if (elementoEstado) {
    elementoEstado.textContent = "Analizando archivo...";
    elementoEstado.className = "ayuda";
  }
  const fd = new FormData();
  fd.append("archivo", archivo);
  try {
    const res = await fetch("/api/metricas/analizar-archivo", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (elementoEstado) {
        elementoEstado.textContent = "❌ " + (data.error || "No se pudo analizar el archivo");
        elementoEstado.className = "ayuda error";
      }
      return null;
    }
    if (elementoEstado) {
      elementoEstado.textContent = `✅ ${data.columnas.length} columna(s) detectada(s).`;
      elementoEstado.className = "ayuda ok";
    }
    return data;
  } catch (err) {
    if (elementoEstado) {
      elementoEstado.textContent = "❌ Error de conexión al analizar el archivo";
      elementoEstado.className = "ayuda error";
    }
    return null;
  }
}

function poblarDatalist(elemento, columnas) {
  elemento.innerHTML = columnas.map((c) => `<option value="${escapeHtml(c)}"></option>`).join("");
}

// ─────────────── IMAGEN DE REFERENCIA (trazabilidad) ───────────────

async function subirImagenMetrica() {
  const archivo = inputImagen.files[0];
  if (!archivo) return;

  estadoImagen.textContent = "Subiendo imagen...";
  estadoImagen.className = "ayuda";

  const fd = new FormData();
  fd.append("imagen", archivo);

  try {
    const res = await fetch("/api/metricas/subir-imagen", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      estadoImagen.textContent = "❌ " + (data.error || "No se pudo subir la imagen");
      estadoImagen.className = "ayuda error";
      return;
    }
    inputImagenRuta.value = data.ruta;
    previewImagenMetrica.src = `/static/${data.ruta}`;
    previewImagenMetrica.classList.remove("oculto");
    estadoImagen.textContent = "✅ Imagen cargada";
    estadoImagen.className = "ayuda ok";
  } catch (err) {
    estadoImagen.textContent = "❌ Error de conexión al subir la imagen";
    estadoImagen.className = "ayuda error";
  }
}

// ─────────────── CONDICIONES (genérico) ───────────────

function crearFilaCondicion(container, datalistId, valores = { columna: "", operador: "distinto", valor: "" }) {
  const row = document.createElement("div");
  row.className = "condicion-row";
  row.innerHTML = `
    <input type="text" class="cond-columna" placeholder="Columna" list="${datalistId}"
           value="${escapeHtml(valores.columna)}">
    <select class="cond-operador">
      ${OPERADORES.map(op => `<option value="${op.valor}" ${op.valor === valores.operador ? "selected" : ""}>${op.texto}</option>`).join("")}
    </select>
    <input type="text" class="cond-valor" placeholder="Valor" value="${escapeHtml(valores.valor)}">
    <button type="button" onclick="this.parentElement.remove()">✕</button>`;
  container.appendChild(row);
}

function leerCondiciones(container) {
  const filas = [...container.querySelectorAll(".condicion-row")].map((row) => ({
    columna: row.querySelector(".cond-columna").value.trim(),
    operador: row.querySelector(".cond-operador").value,
    valor: row.querySelector(".cond-valor").value.trim(),
  })).filter((c) => c.columna);
  return filas.length ? [filas] : [];
}

// ─────────────── SEPARACIÓN POR ENTIDAD ───────────────

function agregarColumnaSeparacion(valor = "") {
  const row = document.createElement("div");
  row.className = "condicion-row";
  row.innerHTML = `
    <input type="text" class="separacion-columna" placeholder="Columna (ej. company)"
           list="datalist-columnas" value="${escapeHtml(valor)}">
    <button type="button" onclick="this.parentElement.remove()">✕</button>`;
  separacionContainer.appendChild(row);
}

function leerColumnasSeparacion() {
  return [...separacionContainer.querySelectorAll(".separacion-columna")]
    .map((input) => input.value.trim())
    .filter((v) => v);
}

// ─────────────── CRUCES (enriquecimientos) ───────────────

function agregarCruce(valores = null) {
  contadorCruce += 1;
  const idDatalist = `datalist-cruce-${contadorCruce}`;
  const box = document.createElement("div");
  box.className = "cruce-box";
  box.dataset.datalist = idDatalist;
  box.innerHTML = `
    <button type="button" class="btn-quitar" onclick="this.parentElement.remove()">✕ Quitar</button>

    <label>Archivo con el que se cruza (súbelo para detectar sus columnas)</label>
    <input type="file" class="cruce-archivo" accept=".xlsx,.xls,.csv">
    <p class="ayuda cruce-estado"></p>

    <label>Patrón del archivo a cruzar</label>
    <input type="text" class="cruce-patron" placeholder="cmdb_ci_computer.xlsx"
           value="${valores ? escapeHtml(valores.archivo_patron) : ""}">

    <label>Columna en ESTA métrica (columna base)</label>
    <input type="text" class="cruce-columna-base" list="datalist-columnas" placeholder="hostname"
           value="${valores ? escapeHtml(valores.columna_base) : ""}">

    <label>Columna en el archivo externo (para cruzar)</label>
    <input type="text" class="cruce-columna-cruzar" list="${idDatalist}" placeholder="Name"
           value="${valores ? escapeHtml(valores.columna_cruzar) : ""}">

    <label>Columnas a traer del archivo externo (ctrl/cmd + click para elegir varias)</label>
    <select class="cruce-columnas-extraer" multiple></select>`;
  enriquecimientosContainer.appendChild(box);

  const inputArchivoCruce = box.querySelector(".cruce-archivo");
  const estadoCruce = box.querySelector(".cruce-estado");
  const selectExtraer = box.querySelector(".cruce-columnas-extraer");

  if (valores && valores.columnas_extraer && valores.columnas_extraer.length) {
    selectExtraer.innerHTML = valores.columnas_extraer
      .map((c) => `<option value="${escapeHtml(c)}" selected>${escapeHtml(c)}</option>`)
      .join("");
  }

  inputArchivoCruce.addEventListener("change", async () => {
    const archivo = inputArchivoCruce.files[0];
    if (!archivo) return;
    const resultado = await analizarArchivo(archivo, estadoCruce);
    if (!resultado) return;

    const datalistCruce = document.createElement("datalist");
    datalistCruce.id = idDatalist;
    poblarDatalist(datalistCruce, resultado.columnas);
    const anterior = document.getElementById(idDatalist);
    if (anterior) anterior.remove();
    box.appendChild(datalistCruce);

    selectExtraer.innerHTML = resultado.columnas
      .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");

    const campoPatron = box.querySelector(".cruce-patron");
    if (!campoPatron.value.trim()) campoPatron.value = resultado.patron_sugerido;
  });
}

function leerCruces() {
  return [...enriquecimientosContainer.querySelectorAll(".cruce-box")].map((box) => ({
    archivo_patron: box.querySelector(".cruce-patron").value.trim(),
    columna_base: box.querySelector(".cruce-columna-base").value.trim(),
    columna_cruzar: box.querySelector(".cruce-columna-cruzar").value.trim(),
    columnas_extraer: [...box.querySelector(".cruce-columnas-extraer").selectedOptions].map((o) => o.value),
  })).filter((c) => c.archivo_patron && c.columna_base && c.columna_cruzar);
}

// ─────────────── MODAL: abrir / cerrar / cargar datos ───────────────

function abrirModal(metrica = null) {
  form.reset();
  condicionesContainer.innerHTML = "";
  limpiezaContainer.innerHTML = "";
  enriquecimientosContainer.innerHTML = "";
  separacionContainer.innerHTML = "";
  favorContainer.innerHTML = "";
  totalContainer.innerHTML = "";
  excluirContainer.innerHTML = "";
  columnasDetectadas = [];
  poblarDatalist(datalistColumnas, columnasDetectadas);
  estadoAnalisis.textContent = "";
  estadoImagen.textContent = "";
  previewImagenMetrica.classList.add("oculto");
  previewImagenMetrica.src = "";
  inputImagenRuta.value = "";
  cumplimientoDetalle.classList.add("oculto");
  cumplimientoAplica.checked = false;
  totalModo.value = "todas";
  totalFijoInput.classList.add("oculto");
  totalContainer.classList.add("oculto");
  btnAgregarTotal.classList.add("oculto");
  document.getElementById("metrica-incluir-reporte").checked = true;

  document.getElementById("metrica-id").value = "";
  document.getElementById("modal-titulo").textContent = metrica ? "Editar métrica" : "Nueva métrica";

  if (metrica) {
    document.getElementById("metrica-id").value = metrica.id;
    document.getElementById("metrica-nombre").value = metrica.nombre;
    document.getElementById("metrica-categoria").value = metrica.categoria || "";
    document.getElementById("metrica-obligatoria").checked = metrica.obligatoria;
    document.getElementById("metrica-incluir-reporte").checked = metrica.incluir_en_reporte !== false;
    document.getElementById("metrica-archivo-patron").value = metrica.archivo_patron;
    document.getElementById("metrica-archivo-respaldo").value = metrica.archivo_respaldo_patron || "";
    document.getElementById("metrica-columna-id").value = metrica.columna_id;
    document.getElementById("metrica-limpiar-id").value = metrica.limpiar_id || "";
    document.getElementById("metrica-instrucciones").value = metrica.instrucciones_descarga || "";
    document.getElementById("metrica-seccion-ppt").value = metrica.seccion_ppt || "";
    document.getElementById("metrica-grupo-visual-ppt").value = metrica.grupo_visual_ppt || "";
    document.getElementById("metrica-titulo-ppt").value = metrica.titulo_ppt || "";

    if (metrica.imagen_instructivo) {
      inputImagenRuta.value = metrica.imagen_instructivo;
      previewImagenMetrica.src = `/static/${metrica.imagen_instructivo}`;
      previewImagenMetrica.classList.remove("oculto");
    }

    (metrica.columnas_separacion || []).forEach((col) => agregarColumnaSeparacion(col));

    const primerGrupo = (metrica.criterios_incumplimiento || [])[0] || [];
    primerGrupo.forEach((c) => crearFilaCondicion(condicionesContainer, "datalist-columnas", c));

    const primerGrupoLimpieza = (metrica.criterios_limpieza || [])[0] || [];
    primerGrupoLimpieza.forEach((c) => crearFilaCondicion(limpiezaContainer, "datalist-columnas", c));

    (metrica.enriquecimientos || []).forEach((e) => agregarCruce(e));

    const cump = metrica.cumplimiento || {};
    if (cump.aplica) {
      cumplimientoAplica.checked = true;
      cumplimientoDetalle.classList.remove("oculto");
      document.getElementById("cumplimiento-operador").value = cump.operador || ">";
      document.getElementById("cumplimiento-umbral").value = cump.umbral ?? 0.97;

      ((cump.criterio_favor || [])[0] || []).forEach((c) =>
        crearFilaCondicion(favorContainer, "datalist-columnas", c));

      if (cump.criterio_total_fijo != null) {
        totalModo.value = "fijo";
        totalFijoInput.value = cump.criterio_total_fijo;
        totalFijoInput.classList.remove("oculto");
      } else if ((cump.criterio_total || []).length) {
        totalModo.value = "condicion";
        totalContainer.classList.remove("oculto");
        btnAgregarTotal.classList.remove("oculto");
        cump.criterio_total[0].forEach((c) =>
          crearFilaCondicion(totalContainer, "datalist-columnas", c));
      } else {
        totalModo.value = "todas";
      }

      ((cump.excluir || [])[0] || []).forEach((c) =>
        crearFilaCondicion(excluirContainer, "datalist-columnas", c));
    }
  } else {
    crearFilaCondicion(condicionesContainer, "datalist-columnas");
    agregarColumnaSeparacion();
  }
  modal.classList.remove("oculto");
}

function cerrarModal() {
  modal.classList.add("oculto");
}

// ─────────────── CRUD ───────────────

async function editarMetrica(id) {
  const res = await fetch(`/api/metricas/${id}`);
  if (!res.ok) return alert("No se pudo cargar la métrica");
  const metrica = await res.json();
  abrirModal(metrica);
}

async function eliminarMetrica(id) {
  if (!confirm("¿Eliminar esta métrica?")) return;
  const res = await fetch(`/api/metricas/${id}`, { method: "DELETE" });
  if (!res.ok) return alert("No se pudo eliminar");
  cargarMetricas();
}

async function guardarMetrica(e) {
  e.preventDefault();

  const cumplimientoPayload = {
    aplica: cumplimientoAplica.checked,
    operador: document.getElementById("cumplimiento-operador").value,
    umbral: parseFloat(document.getElementById("cumplimiento-umbral").value) || 0,
    criterio_favor: leerCondiciones(favorContainer),
    criterio_total: totalModo.value === "condicion" ? leerCondiciones(totalContainer) : [],
    criterio_total_fijo: totalModo.value === "fijo"
      ? (parseInt(totalFijoInput.value, 10) || null) : null,
    excluir: leerCondiciones(excluirContainer),
  };

  const payload = {
    nombre: document.getElementById("metrica-nombre").value.trim(),
    categoria: document.getElementById("metrica-categoria").value.trim(),
    obligatoria: document.getElementById("metrica-obligatoria").checked,
    incluir_en_reporte: document.getElementById("metrica-incluir-reporte").checked,
    archivo_patron: document.getElementById("metrica-archivo-patron").value.trim(),
    archivo_respaldo_patron: document.getElementById("metrica-archivo-respaldo").value.trim() || null,
    columna_id: document.getElementById("metrica-columna-id").value.trim(),
    limpiar_id: document.getElementById("metrica-limpiar-id").value.trim() || null,
    columnas_separacion: leerColumnasSeparacion(),
    criterios_incumplimiento: leerCondiciones(condicionesContainer),
    criterios_limpieza: leerCondiciones(limpiezaContainer),
    enriquecimientos: leerCruces(),
    cumplimiento: cumplimientoPayload,
    funcion_especial: null,
    instrucciones_descarga: document.getElementById("metrica-instrucciones").value.trim(),
    imagen_instructivo: inputImagenRuta.value.trim() || null,
    seccion_ppt: document.getElementById("metrica-seccion-ppt").value.trim(),
    grupo_visual_ppt: document.getElementById("metrica-grupo-visual-ppt").value.trim() || null,
    titulo_ppt: document.getElementById("metrica-titulo-ppt").value.trim() || null,
  };

  const id = document.getElementById("metrica-id").value;
  const url = id ? `/api/metricas/${id}` : "/api/metricas";
  const method = id ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) return alert(data.error || "Error al guardar");

  cerrarModal();
  cargarMetricas();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ─────────────── BANDERAS PPT ───────────────

async function verBanderas(id) {
  const modalB = document.getElementById("modal-banderas");
  const tituloB = document.getElementById("banderas-titulo");
  const listaB = document.getElementById("banderas-lista");

  tituloB.textContent = "Cargando...";
  listaB.innerHTML = "";
  modalB.classList.remove("oculto");

  const res = await fetch(`/api/metricas/${id}/banderas`);
  const data = await res.json();

  if (!res.ok || !data.ok) {
    tituloB.textContent = "Error";
    listaB.innerHTML = `<p class="ayuda error">${escapeHtml(data.error || "No se pudieron cargar las banderas")}</p>`;
    return;
  }

  tituloB.textContent = `Banderas de "${data.metrica}"`;

  if (!data.banderas.length) {
    listaB.innerHTML = "<p class='ayuda'>Esta métrica no genera ninguna bandera todavía (revisa que tenga cumplimiento o esté incluida en el reporte).</p>";
    return;
  }

  listaB.innerHTML = data.banderas.map((b) => `
    <div class="fila-bandera">
      <code class="texto-bandera">&lt;&lt;${escapeHtml(b.bandera)}&gt;&gt;</code>
      <button type="button" class="btn-secundario" onclick="copiarBandera(this, '<<${escapeAttrJs(b.bandera)}>>')">Copiar</button>
      <p class="ayuda">${escapeHtml(b.descripcion)}</p>
    </div>`).join("");
}

function copiarBandera(boton, texto) {
  navigator.clipboard.writeText(texto).then(() => {
    const original = boton.textContent;
    boton.textContent = "✅ Copiado";
    setTimeout(() => { boton.textContent = original; }, 1500);
  });
}

function escapeAttrJs(str) {
  return String(str).replace(/'/g, "\\'");
}

const btnCerrarBanderas = document.getElementById("btn-cerrar-banderas");
if (btnCerrarBanderas) {
  btnCerrarBanderas.addEventListener("click", () => {
    document.getElementById("modal-banderas").classList.add("oculto");
  });
}