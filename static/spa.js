/**
 * Single Page Application para el Programa Sintético NEM
 * Maneja navegación, estado y comunicación con la API de Flask
 */

class ProgramaSinteticoSPA {
  constructor() {
    this.currentPage = "inicio";
    this.currentFase = 3;
    this.currentCampoId = null;
    this.currentContenidoId = null;
    this.campos = [];
    this.history = [];

    this.elements = {
      loading: document.getElementById("loading"),
      errorContainer: document.getElementById("error-container"),
      errorMessage: document.getElementById("error-message"),
      retryBtn: document.getElementById("retry-btn"),
      contentContainer: document.getElementById("content-container"),
      faseSelector: document.getElementById("fase-selector"),
      searchInput: document.getElementById("search-input"),
      searchBtn: document.getElementById("search-btn"),
    };

    this.templates = {
      inicio: document.getElementById("inicio-template"),
      campoCard: document.getElementById("campo-card-template"),
      resumen: document.getElementById("resumen-template"),
      statCard: document.getElementById("stat-card-template"),
      contenidos: document.getElementById("contenidos-template"),
      contenidoItem: document.getElementById("contenido-item-template"),
      detalle: document.getElementById("detalle-template"),
      pdaGroup: document.getElementById("pda-group-template"),
      pdaItem: document.getElementById("pda-item-template"),
      busqueda: document.getElementById("busqueda-template"),
      searchContenido: document.getElementById("search-contenido-template"),
      searchPda: document.getElementById("search-pda-template"),
      filtrar: document.getElementById("filtrar-template"),
      pdaFiltrado: document.getElementById("pda-filtrado-template"),
      inicioPda: document.getElementById("inicio-pda-template"),
    };

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadInitialData();
    this.showPage("inicio");
  }

  setupEventListeners() {
    // Navegación
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const page = e.target.getAttribute("data-page");
        this.showPage(page);
        this.updateActiveNavLink(e.target);
      });
    });

    // Selector de fase
    this.elements.faseSelector.addEventListener("change", (e) => {
      this.currentFase = parseInt(e.target.value);
      this.refreshCurrentPage();
    });

    // Búsqueda
    this.elements.searchBtn.addEventListener("click", () => {
      this.performSearch();
    });

    this.elements.searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.performSearch();
      }
    });

    // Reintentar en caso de error
    this.elements.retryBtn.addEventListener("click", () => {
      this.hideError();
      this.refreshCurrentPage();
    });

    // Navegación del historial del navegador
    window.addEventListener("popstate", (e) => {
      if (e.state) {
        this.restoreState(e.state);
      }
    });
  }

  async loadInitialData() {
    try {
      this.campos = await this.fetchAPI("/api/campos");
    } catch (error) {
      console.error("Error cargando datos iniciales:", error);
    }
  }

  async fetchAPI(endpoint, params = {}) {
    const url = new URL(endpoint, window.location.origin);
    Object.keys(params).forEach((key) => {
      url.searchParams.append(key, params[key]);
    });

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }
    return await response.json();
  }

  showLoading() {
    this.elements.loading.classList.remove("hidden");
    this.elements.contentContainer.classList.add("hidden");
    this.hideError();
  }

  hideLoading() {
    this.elements.loading.classList.add("hidden");
    this.elements.contentContainer.classList.remove("hidden");
  }

  showError(message) {
    this.elements.errorMessage.textContent = message;
    this.elements.errorContainer.classList.remove("hidden");
    this.hideLoading();
  }

  hideError() {
    this.elements.errorContainer.classList.add("hidden");
  }

  updateActiveNavLink(activeLink) {
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.remove("active");
    });
    activeLink.classList.add("active");
  }

  pushState(state) {
    this.history.push(state);
    const url = `#${state.page}${
      state.params ? "?" + new URLSearchParams(state.params).toString() : ""
    }`;
    history.pushState(state, "", url);
  }

  restoreState(state) {
    this.currentPage = state.page;
    this.currentFase = state.fase || 3;
    this.currentCampoId = state.campoId || null;
    this.currentContenidoId = state.contenidoId || null;

    this.elements.faseSelector.value = this.currentFase;
    this.showPage(this.currentPage);
  }

  async showPage(page) {
    this.currentPage = page;
    this.showLoading();

    try {
      switch (page) {
        case "inicio":
          await this.renderInicio();
          break;
        case "resumen":
          await this.renderResumen();
          break;
        case "filtrar":
          await this.renderFiltrar();
          break;
        default:
          throw new Error(`Página desconocida: ${page}`);
      }

      this.pushState({
        page: page,
        fase: this.currentFase,
        campoId: this.currentCampoId,
        contenidoId: this.currentContenidoId,
      });
    } catch (error) {
      console.error("Error mostrando página:", error);
      this.showError(`Error cargando la página: ${error.message}`);
    }
  }

  async renderInicio() {
    const template = this.templates.inicio.content.cloneNode(true);
    const camposGrid = template.getElementById("campos-grid");
    const inicioCampo = template.getElementById("inicio-filtro-campo");

    // Cargar campos si no están cargados
    if (this.campos.length === 0) {
      this.campos = await this.fetchAPI("/api/campos");
    }

    // Poblar selector de filtrado rápido
    this.campos.forEach((campo) => {
      const option = document.createElement("option");
      option.value = campo.id;
      option.textContent = campo.nombre;
      inicioCampo.appendChild(option);
    });

    // Crear tarjetas de campos
    this.campos.forEach((campo) => {
      const campoElement = this.createCampoCard(campo);
      camposGrid.appendChild(campoElement);
    });

    this.elements.contentContainer.innerHTML = "";
    this.elements.contentContainer.appendChild(template);
    this.elements.contentContainer.classList.add("fade-in");
    this.hideLoading();

    // Configurar eventos de los campos y filtrado rápido
    this.setupCampoEvents();
    this.setupFiltroRapidoEvents();
  }

  createCampoCard(campo) {
    const template = this.templates.campoCard.content.cloneNode(true);
    const article = template.querySelector(".campo-card");
    const nombre = template.querySelector(".campo-nombre");
    const descripcion = template.querySelector(".campo-descripcion");
    const button = template.querySelector(".campo-btn");

    article.setAttribute("data-campo-id", campo.id);
    nombre.textContent = campo.nombre;
    descripcion.textContent =
      campo.descripcion || "Campo formativo del Programa Sintético NEM";
    button.setAttribute("data-campo-id", campo.id);
    button.textContent = "Ver Contenidos";

    return template;
  }

  setupCampoEvents() {
    document.querySelectorAll(".campo-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const campoId = parseInt(e.target.getAttribute("data-campo-id"));
        this.showContenidos(campoId);
      });
    });
  }

  setupFiltroRapidoEvents() {
    const inicioCampo = document.getElementById("inicio-filtro-campo");
    const inicioContenido = document.getElementById("inicio-filtro-contenido");
    const aplicarBtn = document.getElementById("inicio-aplicar-filtros");
    const limpiarBtn = document.getElementById("inicio-limpiar-filtros");
    const verMasBtn = document.getElementById("inicio-ver-filtro-completo");

    // Evento para cambio de campo
    inicioCampo.addEventListener("change", async (e) => {
      const campoId = parseInt(e.target.value);
      if (campoId) {
        await this.cargarContenidosInicioFiltro(campoId);
        inicioContenido.disabled = false;
        aplicarBtn.disabled = false;
      } else {
        inicioContenido.innerHTML =
          '<option value="">-- Todos los contenidos --</option>';
        inicioContenido.disabled = true;
        aplicarBtn.disabled = true;
        this.ocultarPdasRapidos();
      }
    });

    // Evento para aplicar filtros
    aplicarBtn.addEventListener("click", async () => {
      const campoId = parseInt(inicioCampo.value);
      const contenidoId = inicioContenido.value
        ? parseInt(inicioContenido.value)
        : null;

      if (campoId) {
        await this.aplicarFiltrosRapidos(campoId, contenidoId);
      }
    });

    // Evento para limpiar filtros
    limpiarBtn.addEventListener("click", () => {
      inicioCampo.value = "";
      inicioContenido.innerHTML =
        '<option value="">-- Todos los contenidos --</option>';
      inicioContenido.disabled = true;
      aplicarBtn.disabled = true;
      this.ocultarPdasRapidos();
    });

    // Evento para ver filtrado completo
    verMasBtn.addEventListener("click", () => {
      this.showPage("filtrar");
      // Pre-seleccionar los valores actuales en la página de filtrado
      setTimeout(() => {
        const filtroCampo = document.getElementById("filtro-campo");
        const filtroContenido = document.getElementById("filtro-contenido");
        if (filtroCampo && inicioCampo.value) {
          filtroCampo.value = inicioCampo.value;
          filtroCampo.dispatchEvent(new Event("change"));
          if (filtroContenido && inicioContenido.value) {
            setTimeout(() => {
              filtroContenido.value = inicioContenido.value;
            }, 200);
          }
        }
      }, 100);
    });
  }

  async cargarContenidosInicioFiltro(campoId) {
    try {
      const contenidos = await this.fetchAPI("/api/contenidos", {
        campo_id: campoId,
        fase: this.currentFase,
      });

      const inicioContenido = document.getElementById(
        "inicio-filtro-contenido"
      );
      inicioContenido.innerHTML =
        '<option value="">-- Todos los contenidos --</option>';

      contenidos.forEach((contenido) => {
        const option = document.createElement("option");
        option.value = contenido.id;
        option.textContent = `${contenido.numero}. ${contenido.titulo}`;
        inicioContenido.appendChild(option);
      });
    } catch (error) {
      console.error("Error cargando contenidos para filtro rápido:", error);
    }
  }

  async aplicarFiltrosRapidos(campoId, contenidoId = null) {
    try {
      const params = {
        campo_id: campoId,
        fase: this.currentFase,
      };

      if (contenidoId) {
        params.contenido_id = contenidoId;
      }

      const pdas = await this.fetchAPI("/api/pdas/filtrados", params);

      this.mostrarPdasRapidos(pdas);
    } catch (error) {
      console.error("Error aplicando filtros rápidos:", error);
    }
  }

  mostrarPdasRapidos(pdas) {
    const container = document.getElementById("inicio-pdas-resultados");
    const count = document.getElementById("inicio-pdas-count");
    const lista = document.getElementById("inicio-pdas-lista");

    count.textContent = pdas.length;
    lista.innerHTML = "";

    if (pdas.length === 0) {
      lista.innerHTML =
        '<div class="empty-state"><p>No se encontraron PDAs con los filtros seleccionados.</p></div>';
    } else {
      // Mostrar solo los primeros 5 resultados en la página de inicio
      const pdasLimitados = pdas.slice(0, 5);
      pdasLimitados.forEach((pda) => {
        const pdaElement = this.createInicioPdaItem(pda);
        lista.appendChild(pdaElement);
      });

      // Configurar eventos de los botones
      this.setupInicioPdaEvents();
    }

    container.classList.remove("hidden");

    // Scroll suave al contenedor de resultados
    container.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  createInicioPdaItem(pda) {
    const template = this.templates.inicioPda.content.cloneNode(true);
    const numero = template.querySelector(".inicio-pda-numero");
    const grado = template.querySelector(".inicio-pda-grado");
    const contenidoInfo = template.querySelector(".inicio-pda-contenido");
    const descripcion = template.querySelector(".inicio-pda-descripcion");
    const badge = template.querySelector(".inicio-pda-badge");
    const verBtn = template.querySelector(".inicio-ver-contenido-btn");

    numero.textContent = pda.numero_pda;
    grado.textContent = pda.grado;
    contenidoInfo.textContent = `${pda.contenido.numero}. ${pda.contenido.titulo}`;
    descripcion.textContent =
      pda.descripcion.length > 150
        ? pda.descripcion.substring(0, 150) + "..."
        : pda.descripcion;
    badge.textContent = pda.campo;
    verBtn.setAttribute("data-contenido-id", pda.contenido.id);

    return template;
  }

  setupInicioPdaEvents() {
    document.querySelectorAll(".inicio-ver-contenido-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const contenidoId = parseInt(
          e.target.getAttribute("data-contenido-id")
        );
        this.showDetalle(contenidoId);
      });
    });
  }

  ocultarPdasRapidos() {
    const container = document.getElementById("inicio-pdas-resultados");
    if (container) {
      container.classList.add("hidden");
    }
  }

  async renderResumen() {
    const data = await this.fetchAPI("/api/resumen", {
      fase: this.currentFase,
    });
    const template = this.templates.resumen.content.cloneNode(true);
    const faseNumero = template.getElementById("fase-numero");
    const statsGrid = template.getElementById("resumen-stats");

    faseNumero.textContent = this.currentFase;

    data.forEach((stat) => {
      const statElement = this.createStatCard(stat);
      statsGrid.appendChild(statElement);
    });

    this.elements.contentContainer.innerHTML = "";
    this.elements.contentContainer.appendChild(template);
    this.elements.contentContainer.classList.add("fade-in");
    this.hideLoading();

    // Configurar eventos de las tarjetas de estadísticas
    this.setupStatEvents();
  }

  createStatCard(stat) {
    const template = this.templates.statCard.content.cloneNode(true);
    const campo = template.querySelector(".stat-campo");
    const contenidos = template.querySelector(".stat-contenidos");
    const pdas = template.querySelector(".stat-pdas");
    const button = template.querySelector(".campo-btn");

    campo.textContent = stat.campo_nombre;
    contenidos.textContent = stat.num_contenidos;
    pdas.textContent = stat.num_pdas;
    button.setAttribute("data-campo-id", stat.campo_id);

    return template;
  }

  setupStatEvents() {
    document.querySelectorAll(".stat-card .campo-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const campoId = parseInt(e.target.getAttribute("data-campo-id"));
        this.showContenidos(campoId);
      });
    });
  }

  async showContenidos(campoId) {
    this.currentCampoId = campoId;
    this.showLoading();

    try {
      const contenidos = await this.fetchAPI("/api/contenidos", {
        campo_id: campoId,
        fase: this.currentFase,
      });

      const campo = this.campos.find((c) => c.id === campoId);
      const template = this.templates.contenidos.content.cloneNode(true);
      const titulo = template.getElementById("campo-titulo");
      const lista = template.getElementById("contenidos-list");
      const backBtn = template.getElementById("back-btn");

      titulo.textContent = campo ? campo.nombre : `Campo ${campoId}`;

      if (contenidos.length === 0) {
        lista.innerHTML =
          '<div class="empty-state"><h3>Sin contenidos</h3><p>No hay contenidos disponibles para este campo en la fase seleccionada.</p></div>';
      } else {
        contenidos.forEach((contenido) => {
          const contenidoElement = this.createContenidoItem(contenido);
          lista.appendChild(contenidoElement);
        });
      }

      this.elements.contentContainer.innerHTML = "";
      this.elements.contentContainer.appendChild(template);
      this.elements.contentContainer.classList.add("fade-in");
      this.hideLoading();

      // Configurar eventos
      this.setupContenidoEvents();
      backBtn.addEventListener("click", () => {
        this.showPage(this.currentPage);
      });
    } catch (error) {
      console.error("Error cargando contenidos:", error);
      this.showError(`Error cargando contenidos: ${error.message}`);
    }
  }

  createContenidoItem(contenido) {
    const template = this.templates.contenidoItem.content.cloneNode(true);
    const article = template.querySelector(".contenido-item");
    const numero = template.querySelector(".contenido-numero");
    const titulo = template.querySelector(".contenido-titulo");
    const button = template.querySelector(".contenido-btn");

    article.setAttribute("data-contenido-id", contenido.id);
    numero.textContent = contenido.numero;
    titulo.textContent = contenido.titulo;
    button.setAttribute("data-contenido-id", contenido.id);

    return template;
  }

  setupContenidoEvents() {
    document.querySelectorAll(".contenido-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const contenidoId = parseInt(
          e.target.getAttribute("data-contenido-id")
        );
        this.showDetalle(contenidoId);
      });
    });
  }

  async showDetalle(contenidoId) {
    this.currentContenidoId = contenidoId;
    this.showLoading();

    try {
      const data = await this.fetchAPI(`/api/contenidos/${contenidoId}`);
      const template = this.templates.detalle.content.cloneNode(true);
      const titulo = template.getElementById("detalle-titulo");
      const campo = template.getElementById("detalle-campo");
      const fase = template.getElementById("detalle-fase");
      const pdasContainer = template.getElementById("pdas-container");
      const backBtn = template.getElementById("back-to-contenidos-btn");

      titulo.textContent = `${data.numero}. ${data.titulo}`;
      campo.textContent = data.campo;
      fase.textContent = data.fase;

      // Agrupar PDAs por grado
      const pdasPorGrado = {};
      data.pdas.forEach((pda) => {
        if (!pdasPorGrado[pda.grado]) {
          pdasPorGrado[pda.grado] = [];
        }
        pdasPorGrado[pda.grado].push(pda);
      });

      if (Object.keys(pdasPorGrado).length === 0) {
        pdasContainer.innerHTML =
          '<div class="empty-state"><h3>Sin PDAs</h3><p>No hay Procesos de Desarrollo de Aprendizaje disponibles para este contenido.</p></div>';
      } else {
        Object.keys(pdasPorGrado).forEach((grado) => {
          const grupoElement = this.createPdaGroup(grado, pdasPorGrado[grado]);
          pdasContainer.appendChild(grupoElement);
        });
      }

      this.elements.contentContainer.innerHTML = "";
      this.elements.contentContainer.appendChild(template);
      this.elements.contentContainer.classList.add("fade-in");
      this.hideLoading();

      // Configurar evento del botón volver
      backBtn.addEventListener("click", () => {
        this.showContenidos(this.currentCampoId);
      });
    } catch (error) {
      console.error("Error cargando detalle:", error);
      this.showError(`Error cargando detalle: ${error.message}`);
    }
  }

  createPdaGroup(grado, pdas) {
    const template = this.templates.pdaGroup.content.cloneNode(true);
    const gradoElement = template.querySelector(".pda-grado");
    const lista = template.querySelector(".pdas-list");

    gradoElement.textContent = grado;

    pdas.forEach((pda) => {
      const pdaElement = this.createPdaItem(pda);
      lista.appendChild(pdaElement);
    });

    return template;
  }

  createPdaItem(pda) {
    const template = this.templates.pdaItem.content.cloneNode(true);
    const numero = template.querySelector(".pda-numero");
    const descripcion = template.querySelector(".pda-descripcion");

    numero.textContent = pda.numero_pda;
    descripcion.textContent = pda.descripcion;

    return template;
  }

  async performSearch() {
    const query = this.elements.searchInput.value.trim();
    if (!query) return;

    this.showLoading();

    try {
      const data = await this.fetchAPI("/api/buscar", {
        q: query,
        fase: this.currentFase,
      });

      this.renderSearchResults(query, data);
    } catch (error) {
      console.error("Error en búsqueda:", error);
      this.showError(`Error en búsqueda: ${error.message}`);
    }
  }

  renderSearchResults(query, data) {
    const template = this.templates.busqueda.content.cloneNode(true);
    const queryText = template.getElementById("query-text");
    const contenidosFound = template.getElementById("contenidos-found");
    const pdasFound = template.getElementById("pdas-found");

    queryText.textContent = query;

    // Renderizar contenidos encontrados
    if (data.contenidos.length === 0) {
      contenidosFound.innerHTML =
        '<div class="empty-state"><p>No se encontraron contenidos.</p></div>';
    } else {
      data.contenidos.forEach((contenido) => {
        const element = this.createSearchContenidoItem(contenido);
        contenidosFound.appendChild(element);
      });
    }

    // Renderizar PDAs encontrados
    if (data.pdas.length === 0) {
      pdasFound.innerHTML =
        '<div class="empty-state"><p>No se encontraron PDAs.</p></div>';
    } else {
      data.pdas.forEach((pda) => {
        const element = this.createSearchPdaItem(pda);
        pdasFound.appendChild(element);
      });
    }

    this.elements.contentContainer.innerHTML = "";
    this.elements.contentContainer.appendChild(template);
    this.elements.contentContainer.classList.add("fade-in");
    this.hideLoading();

    // Configurar eventos de los resultados
    this.setupSearchResultEvents();
  }

  async renderFiltrar() {
    const template = this.templates.filtrar.content.cloneNode(true);
    const faseNumero = template.getElementById("filtrar-fase-numero");
    const filtroCampo = template.getElementById("filtro-campo");
    const filtroContenido = template.getElementById("filtro-contenido");
    const aplicarBtn = template.getElementById("aplicar-filtros");
    const limpiarBtn = template.getElementById("limpiar-filtros");
    const pdasContainer = template.getElementById("pdas-filtrados-container");

    faseNumero.textContent = this.currentFase;

    // Cargar campos si no están cargados
    if (this.campos.length === 0) {
      this.campos = await this.fetchAPI("/api/campos");
    }

    // Poblar selector de campos
    this.campos.forEach((campo) => {
      const option = document.createElement("option");
      option.value = campo.id;
      option.textContent = campo.nombre;
      filtroCampo.appendChild(option);
    });

    this.elements.contentContainer.innerHTML = "";
    this.elements.contentContainer.appendChild(template);
    this.elements.contentContainer.classList.add("fade-in");
    this.hideLoading();

    // Configurar eventos de filtrado
    this.setupFiltroEvents();
  }

  setupFiltroEvents() {
    const filtroCampo = document.getElementById("filtro-campo");
    const filtroContenido = document.getElementById("filtro-contenido");
    const aplicarBtn = document.getElementById("aplicar-filtros");
    const limpiarBtn = document.getElementById("limpiar-filtros");

    // Evento para cambio de campo
    filtroCampo.addEventListener("change", async (e) => {
      const campoId = parseInt(e.target.value);
      if (campoId) {
        await this.cargarContenidosFiltro(campoId);
        filtroContenido.disabled = false;
        aplicarBtn.disabled = false;
      } else {
        filtroContenido.innerHTML =
          '<option value="">-- Todos los contenidos --</option>';
        filtroContenido.disabled = true;
        aplicarBtn.disabled = true;
        this.ocultarPdasFiltrados();
      }
    });

    // Evento para aplicar filtros
    aplicarBtn.addEventListener("click", async () => {
      const campoId = parseInt(filtroCampo.value);
      const contenidoId = filtroContenido.value
        ? parseInt(filtroContenido.value)
        : null;

      if (campoId) {
        await this.aplicarFiltrosPDAs(campoId, contenidoId);
      }
    });

    // Evento para limpiar filtros
    limpiarBtn.addEventListener("click", () => {
      filtroCampo.value = "";
      filtroContenido.innerHTML =
        '<option value="">-- Todos los contenidos --</option>';
      filtroContenido.disabled = true;
      aplicarBtn.disabled = true;
      this.ocultarPdasFiltrados();
    });
  }

  async cargarContenidosFiltro(campoId) {
    try {
      const contenidos = await this.fetchAPI("/api/contenidos", {
        campo_id: campoId,
        fase: this.currentFase,
      });

      const filtroContenido = document.getElementById("filtro-contenido");
      filtroContenido.innerHTML =
        '<option value="">-- Todos los contenidos --</option>';

      contenidos.forEach((contenido) => {
        const option = document.createElement("option");
        option.value = contenido.id;
        option.textContent = `${contenido.numero}. ${contenido.titulo}`;
        filtroContenido.appendChild(option);
      });
    } catch (error) {
      console.error("Error cargando contenidos para filtro:", error);
      this.showError(`Error cargando contenidos: ${error.message}`);
    }
  }

  async aplicarFiltrosPDAs(campoId, contenidoId = null) {
    try {
      this.showLoading();

      const params = {
        campo_id: campoId,
        fase: this.currentFase,
      };

      if (contenidoId) {
        params.contenido_id = contenidoId;
      }

      const pdas = await this.fetchAPI("/api/pdas/filtrados", params);

      this.mostrarPdasFiltrados(pdas);
      this.hideLoading();
    } catch (error) {
      console.error("Error aplicando filtros:", error);
      this.showError(`Error aplicando filtros: ${error.message}`);
    }
  }

  mostrarPdasFiltrados(pdas) {
    const container = document.getElementById("pdas-filtrados-container");
    const count = document.getElementById("pdas-count");
    const list = document.getElementById("pdas-filtrados-list");

    count.textContent = pdas.length;
    list.innerHTML = "";

    if (pdas.length === 0) {
      list.innerHTML =
        '<div class="empty-state"><h3>Sin PDAs</h3><p>No se encontraron Procesos de Desarrollo de Aprendizaje con los filtros seleccionados.</p></div>';
    } else {
      pdas.forEach((pda) => {
        const pdaElement = this.createPdaFiltrado(pda);
        list.appendChild(pdaElement);
      });

      // Configurar eventos de los botones "Ver Contenido Completo"
      this.setupPdaFiltradoEvents();
    }

    container.classList.remove("hidden");

    // Scroll suave al contenedor de resultados
    container.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  createPdaFiltrado(pda) {
    const template = this.templates.pdaFiltrado.content.cloneNode(true);
    const numero = template.querySelector(".pda-numero-filtrado");
    const grado = template.querySelector(".pda-grado-filtrado");
    const contenidoInfo = template.querySelector(".pda-contenido-info");
    const descripcion = template.querySelector(".pda-descripcion-filtrada");
    const campoBadge = template.querySelector(".pda-campo-badge");
    const verBtn = template.querySelector(".ver-contenido-btn");

    numero.textContent = pda.numero_pda;
    grado.textContent = pda.grado;
    contenidoInfo.textContent = `${pda.contenido.numero}. ${pda.contenido.titulo}`;
    descripcion.textContent = pda.descripcion;
    campoBadge.textContent = pda.campo;
    verBtn.setAttribute("data-contenido-id", pda.contenido.id);

    return template;
  }

  setupPdaFiltradoEvents() {
    document.querySelectorAll(".ver-contenido-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const contenidoId = parseInt(
          e.target.getAttribute("data-contenido-id")
        );
        this.showDetalle(contenidoId);
      });
    });
  }

  ocultarPdasFiltrados() {
    const container = document.getElementById("pdas-filtrados-container");
    if (container) {
      container.classList.add("hidden");
    }
  }

  createSearchContenidoItem(contenido) {
    const template = this.templates.searchContenido.content.cloneNode(true);
    const titulo = template.querySelector(".result-titulo");
    const meta = template.querySelector(".result-meta");
    const button = template.querySelector(".result-btn");

    titulo.textContent = `${contenido.numero}. ${contenido.titulo}`;
    meta.textContent = contenido.campo;
    button.setAttribute("data-contenido-id", contenido.id);

    return template;
  }

  createSearchPdaItem(pda) {
    const template = this.templates.searchPda.content.cloneNode(true);
    const titulo = template.querySelector(".result-titulo");
    const meta = template.querySelector(".result-meta");
    const descripcion = template.querySelector(".result-descripcion");
    const button = template.querySelector(".result-btn");

    titulo.textContent = `${pda.titulo} - ${pda.grado}`;
    meta.textContent = `${pda.campo} • PDA ${pda.numero_pda}`;
    descripcion.textContent = pda.descripcion;
    button.setAttribute("data-contenido-id", pda.contenido_id);

    return template;
  }

  setupSearchResultEvents() {
    document.querySelectorAll(".result-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const contenidoId = parseInt(
          e.target.getAttribute("data-contenido-id")
        );
        this.showDetalle(contenidoId);
      });
    });
  }

  refreshCurrentPage() {
    if (this.currentPage === "filtrar") {
      // Para la página de filtrado, necesitamos preservar los filtros actuales
      this.renderFiltrar();
    } else {
      this.showPage(this.currentPage);
    }
  }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  window.spa = new ProgramaSinteticoSPA();
});
