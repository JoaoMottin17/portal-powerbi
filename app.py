import os
import re
import base64
import functools
from html import escape
from datetime import datetime, timedelta, timezone

import streamlit as st
import streamlit.components.v1 as components
from database import Database, CATEGORIAS_PADRAO, NIVEIS_HIERARQUIA, NIVEL_LABELS


# Fuso de Brasilia (UTC-3, sem horario de verao desde 2019).
_TZ_BR = timezone(timedelta(hours=-3))


def fmt_data(valor):
    """Formata datas do Supabase (ISO/UTC) em dd/mm/aaaa hh:mm (horario de Brasilia)."""
    if not valor:
        return "—"
    try:
        dt = valor
        if isinstance(valor, str):
            dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.astimezone(_TZ_BR)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:  # noqa: BLE001  (formato inesperado: mostra o cru)
        return str(valor)[:16].replace("T", " ")


def _icone_aba():
    """Favicon padrao da aba (cabeca de boi verde), usado na carga inicial.
    A troca dinamica conforme o tema do SISTEMA e feita por JavaScript em
    _injetar_favicon_tema()."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boi_escuro.png")
    if os.path.exists(caminho):
        try:
            from PIL import Image
            return Image.open(caminho)
        except Exception:  # noqa: BLE001
            return caminho
    return ":bar_chart:"


@functools.lru_cache(maxsize=None)
def _favicon_data_uris():
    """Le os PNGs do boi e devolve data URIs base64 (verde e branco)."""
    base = os.path.dirname(os.path.abspath(__file__))
    uris = {"verde": "", "branco": ""}
    for chave, nome in (("verde", "boi_escuro.png"), ("branco", "boi_claro.png")):
        caminho = os.path.join(base, nome)
        try:
            with open(caminho, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode("ascii")
            uris[chave] = "data:image/png;base64," + b64
        except Exception:  # noqa: BLE001
            uris[chave] = ""
    return uris


def _injetar_favicon_tema():
    """Troca o favicon da aba conforme o tema do SISTEMA (prefers-color-scheme):
    cabeca de boi VERDE no tema claro, BRANCA no tema escuro. Atualiza ao vivo,
    sem depender do tema (fixo) do Streamlit."""
    uris = _favicon_data_uris()
    if not uris["verde"] and not uris["branco"]:
        return
    js = """
    <script>
    (function () {
      try {
        var doc = window.parent.document;
        var VERDE = "__VERDE__";
        var BRANCO = "__BRANCO__";
        var mq = window.matchMedia("(prefers-color-scheme: dark)");
        function aplicar() {
          var href = (mq.matches ? BRANCO : VERDE) || VERDE || BRANCO;
          if (!href) return;
          var links = doc.querySelectorAll("link[rel~='icon']");
          if (!links.length) {
            var l = doc.createElement("link");
            l.setAttribute("rel", "icon");
            doc.head.appendChild(l);
            links = [l];
          }
          links.forEach(function (link) {
            if (link.getAttribute("href") !== href) {
              link.setAttribute("type", "image/png");
              link.setAttribute("href", href);
            }
          });
        }
        aplicar();
        if (mq.addEventListener) { mq.addEventListener("change", aplicar); }
        else if (mq.addListener) { mq.addListener(aplicar); }
        new MutationObserver(aplicar).observe(doc.head, {
          childList: true, subtree: true, attributes: true, attributeFilter: ["href"]
        });
      } catch (e) {}
    })();
    </script>
    """
    js = js.replace("__VERDE__", uris["verde"]).replace("__BRANCO__", uris["branco"])
    components.html(js, height=0, width=0)


def _ocultar_acoes_github_toolbar():
    """Esconde o icone 'ver codigo-fonte no GitHub' (e os botoes Share/favoritar)
    que o Streamlit Community Cloud injeta na barra superior de apps de
    repositorio PUBLICO.

    ATENCAO: isto e apenas COSMETICO. O repositorio continua publico e
    acessivel diretamente no GitHub (busca, URL, etc.). Para realmente
    proteger o codigo-fonte, torne o repositorio privado."""
    # 1) CSS no documento principal (a toolbar fica no mesmo DOM do app).
    st.markdown(
        """
        <style>
          /* Link de codigo-fonte do GitHub na barra superior */
          [data-testid="stToolbar"] a[href*="github.com"],
          [data-testid="stToolbarActions"] a[href*="github.com"] {
              display: none !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # 2) Reforco via JS no documento-pai: cobre botoes sem href (icone via
    #    onClick) e re-renderizacoes. Mesmo padrao usado no favicon.
    components.html(
        """
        <script>
        (function () {
          try {
            var doc = window.parent.document;
            function esconder() {
              var sels = '[data-testid="stToolbar"] a, [data-testid="stToolbar"] button,'
                       + '[data-testid="stToolbarActions"] a, [data-testid="stToolbarActions"] button';
              doc.querySelectorAll(sels).forEach(function (el) {
                var txt = ((el.getAttribute("href") || "") + " "
                         + (el.getAttribute("aria-label") || "") + " "
                         + (el.getAttribute("title") || "") + " "
                         + (el.textContent || "")).toLowerCase();
                if (txt.indexOf("github") !== -1 || txt.indexOf("source") !== -1
                    || txt.indexOf("fonte") !== -1 || txt.indexOf("fork") !== -1) {
                  el.style.display = "none";
                }
              });
            }
            esconder();
            new MutationObserver(esconder).observe(doc.body, {childList: true, subtree: true});
          } catch (e) {}
        })();
        </script>
        """,
        height=0, width=0,
    )


st.set_page_config(
    page_title="Portal Power BI - Grupo FRT",
    page_icon=_icone_aba(),
    layout="wide",
)

_injetar_favicon_tema()
_ocultar_acoes_github_toolbar()


MENU_DASHBOARD = "Dashboard"
MENU_NOVO_RELATORIO = "Novo relatorio"
MENU_GERENCIAR_USUARIOS = "Usuarios"
MENU_MINHA_CONTA = "Minha conta"


@st.cache_resource
def get_database() -> Database:
    # Bump deste marcador quando o schema/contrato do Database mudar: altera o
    # hash da funcao e forca o Streamlit a recriar o recurso (evita instancia
    # antiga em cache apos um deploy).
    _schema_version = "v3"
    return Database()


try:
    db = get_database()
except Exception as e:  # noqa: BLE001
    st.error(
        "Erro ao conectar/inicializar o Supabase. Confira os secrets "
        "(SUPABASE_URL/SUPABASE_KEY) e o schema (supabase_schema.sql / migration_v3.sql)."
    )
    st.exception(e)
    st.stop()


# Leituras usadas na gestao de usuarios. Cacheadas para a tela nao bater no
# Supabase a cada rerun (evita lentidao); o cache e limpado nas gravacoes.
@st.cache_data(ttl=120, show_spinner=False)
def cached_listar_usuarios():
    return db.listar_usuarios()


@st.cache_data(ttl=120, show_spinner=False)
def cached_listar_relatorios_basico():
    return db.listar_relatorios_basico()


def render_logo(width: int, path: str = "logo.png", use_container_width: bool = False):
    if os.path.exists(path):
        if use_container_width:
            st.image(path, use_container_width=True)
        else:
            st.image(path, width=width)


def render_logo_janelas(width: int = 520):
    if os.path.exists("logo_janelas_1.png"):
        janelas_logo = "logo_janelas_1.png"
    else:
        janelas_logo = "logo.png"
    render_logo(width, janelas_logo)


def render_logo_centered(path: str, max_width: int, top_margin: int = 0):
    if not os.path.exists(path):
        return
    with open(path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin-top:{top_margin}px;">
            <img src="data:image/png;base64,{encoded}"
                 style="width:min({max_width}px, 92%);height:auto;object-fit:contain;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_professional_theme():
    st.markdown(
        """
        <style>
            /* ---- Tipografia profissional (Poppins nos titulos + Inter no corpo) ---- */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
            .material-symbols-outlined {
                font-family: 'Material Symbols Outlined';
                font-weight: normal; font-style: normal; line-height: 1;
                vertical-align: middle; -webkit-font-feature-settings: 'liga';
            }

            :root {
                --frt-escuro: #14401E;   /* verde escuro da logo */
                --frt-verde:  #2E7D32;
                --frt-medio:  #43A047;   /* faixa media da logo */
                --frt-claro:  #7CB342;   /* faixa clara da logo */
                --frt-bg:     #F5F8F4;
                --frt-card:   #FFFFFF;
                --frt-borda:  #E2E8E0;
                --frt-texto:  #1D2A22;
                --frt-suave:  #5B6B60;
            }

            html, body, .stApp, [data-testid="stSidebar"],
            input, textarea, button, select, [data-baseweb] {
                font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
            }
            h1, h2, h3, h4, .portal-title, .sidebar-brand {
                font-family: 'Poppins', 'Inter', sans-serif !important;
                color: var(--frt-escuro);
                letter-spacing: -0.01em;
            }

            /* ---- Fundo e barra superior ---- */
            .stApp { background: var(--frt-bg); }
            [data-testid="stHeader"] {
                background: #FFFFFF;
                border-bottom: 3px solid var(--frt-medio);
            }
            .block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.4rem; }

            /* ---- Sidebar ---- */
            [data-testid="stSidebar"] {
                background: #FFFFFF;
                border-right: 1px solid var(--frt-borda);
            }
            [data-testid="stSidebar"] [data-testid="stImage"] { margin-bottom: 0 !important; }
            .sidebar-brand {
                margin: -0.35rem 0 0.05rem 0; text-align: center;
                font-size: 2rem; font-weight: 700;
            }
            .sidebar-subtitle {
                margin: 0 0 0.1rem 0; text-align: center; color: var(--frt-suave);
                font-size: 0.82rem; font-weight: 600; letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            .sidebar-user { margin: 0; color: var(--frt-texto); font-size: 1rem; font-weight: 600; }

            /* ---- Titulos do conteudo ---- */
            .portal-kicker { margin: 0; text-align: center; color: var(--frt-suave);
                font-size: 0.95rem; font-weight: 500; }
            .portal-title {
                margin: 0.2rem 0 0.8rem 0; text-align: center;
                font-size: 2.4rem; font-weight: 700;
            }

            /* ---- Botoes ---- */
            .stButton > button {
                border-radius: 10px; font-weight: 600; transition: all .15s ease;
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, var(--frt-escuro) 0%, var(--frt-medio) 100%);
                border: none; color: #ffffff; font-weight: 700;
                box-shadow: 0 2px 6px rgba(20,64,30,.25);
            }
            .stButton > button[kind="primary"]:hover {
                filter: brightness(1.07); transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(20,64,30,.3);
            }
            .stButton > button[kind="secondary"] { border: 1px solid var(--frt-borda); }
            .stButton > button[kind="secondary"]:hover {
                border-color: var(--frt-medio); color: var(--frt-escuro);
            }

            /* Navegacao da sidebar: itens alinhados a esquerda, estilo menu */
            [data-testid="stSidebar"] .stButton > button {
                justify-content: flex-start;
                padding-left: 0.9rem;
                font-weight: 600;
            }
            [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
                border-color: transparent;
                background: transparent;
                color: var(--frt-texto);
            }
            [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
                background: #F0F5EE;
                border-color: transparent;
            }

            /* ---- Cards / expanders (lista de relatorios) ---- */
            [data-testid="stExpander"] {
                border: 1px solid var(--frt-borda) !important;
                border-radius: 12px !important;
                background: var(--frt-card);
                box-shadow: 0 1px 3px rgba(20,64,30,.06);
                transition: box-shadow .15s ease, transform .15s ease, border-color .15s ease;
                overflow: hidden;
            }
            [data-testid="stExpander"]:hover {
                box-shadow: 0 6px 18px rgba(20,64,30,.12);
                border-color: var(--frt-claro) !important;
                transform: translateY(-1px);
            }
            [data-testid="stExpander"] summary { font-weight: 600; color: var(--frt-escuro); }
            [data-testid="stExpander"] summary:hover { color: var(--frt-medio); }

            /* Cards (grade de relatorios e listas) */
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 14px !important;
                box-shadow: 0 1px 3px rgba(20,64,30,.06);
                transition: box-shadow .18s ease, transform .18s ease, border-color .18s ease;
            }
            [data-testid="stVerticalBlockBorderWrapper"]:hover {
                box-shadow: 0 10px 24px rgba(20,64,30,.13);
                transform: translateY(-2px);
            }

            /* ---- Inputs com foco verde ---- */
            [data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within,
            [data-baseweb="textarea"]:focus-within, .stTextArea textarea:focus {
                border-color: var(--frt-medio) !important;
                box-shadow: 0 0 0 2px rgba(67,160,71,.18) !important;
            }

            /* ---- Detalhes ---- */
            [data-baseweb="tag"] { background-color: var(--frt-medio) !important; }
            hr { border-color: var(--frt-borda); }
            .stAlert { border-radius: 10px; }

            [data-testid="stSidebar"] img,
            [data-testid="stMainBlockContainer"] img {
                object-fit: contain !important;
                height: auto !important;
                max-width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_sidebar_visibility():
    if st.session_state.get("ocultar_sidebar", False):
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] { display: none !important; }
                [data-testid="stSidebarCollapsedControl"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def render_page_header(title_text: str):
    if os.path.exists("logo_janelas_1.png"):
        logo_path = "logo_janelas_1.png"
    else:
        logo_path = "logo.png"
    render_logo_centered(logo_path, 460, top_margin=42)
    st.markdown(f'<h1 class="portal-title">{title_text}</h1>', unsafe_allow_html=True)


def verificar_login(username: str, senha: str):
    return db.autenticar_usuario(username, senha)


def listar_relatorios(usuario):
    return db.listar_relatorios_usuario(usuario)


def obter_relatorio_por_id(relatorio_id: int, usuario=None):
    return db.obter_relatorio_por_id(relatorio_id, usuario)


def listar_relatorios_basico():
    return db.listar_relatorios_basico()


def criar_relatorio(titulo, link_powerbi, descricao, categoria, criado_por, nivel_hierarquia):
    try:
        ok = db.criar_relatorio(
            titulo, link_powerbi, descricao, categoria, criado_por, nivel_hierarquia
        )
        if ok:
            cached_listar_relatorios_basico.clear()
        return ok
    except Exception as e:
        st.error(f"Erro ao criar relatorio: {e}")
        return False


def atualizar_relatorio(relatorio_id, titulo, link_powerbi, descricao, categoria, nivel_hierarquia):
    try:
        ok = db.atualizar_relatorio(
            relatorio_id, titulo, link_powerbi, descricao, categoria, nivel_hierarquia
        )
        if ok:
            cached_listar_relatorios_basico.clear()
        return ok
    except Exception as e:
        st.error(f"Erro ao atualizar relatorio: {e}")
        return False


def categorias_disponiveis_para(usuario):
    """Areas que o usuario pode atribuir a um relatorio (admin = todas)."""
    if usuario.get("is_admin"):
        return list(CATEGORIAS_PADRAO)
    return list(usuario.get("categorias_permitidas") or ["GERAL"])


def niveis_disponiveis_para(usuario):
    """Niveis hierarquicos que o usuario pode atribuir (operacao so cria operacao)."""
    if usuario.get("is_admin") or usuario.get("nivel_hierarquia") == "gestao":
        return list(NIVEIS_HIERARQUIA)
    return ["operacao"]


def excluir_relatorio(relatorio_id):
    try:
        ok = db.excluir_relatorio(relatorio_id)
        if ok:
            cached_listar_relatorios_basico.clear()
        return ok
    except Exception as e:
        st.error(f"Erro ao excluir relatorio: {e}")
        return False


def listar_usuarios():
    return db.listar_usuarios()


def obter_usuario_por_id(usuario_id):
    return db.obter_usuario_por_id(usuario_id)


def criar_usuario(username, senha, is_admin=False, nivel_hierarquia="operacao",
                  categorias_permitidas=None, relatorios_permitidos=None):
    try:
        ok = db.criar_usuario_portal(
            username, senha, is_admin, nivel_hierarquia,
            categorias_permitidas, relatorios_permitidos,
        )
        if ok:
            cached_listar_usuarios.clear()
        return ok
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            st.error("Este nome de usuario ja existe.")
        else:
            st.error(f"Erro ao criar usuario: {e}")
        return False


def atualizar_usuario(usuario_id, username=None, is_admin=None, nivel_hierarquia=None,
                      categorias_permitidas=None, relatorios_permitidos=None):
    try:
        ok = db.atualizar_usuario_portal(
            usuario_id, username, is_admin, nivel_hierarquia,
            categorias_permitidas, relatorios_permitidos,
        )
        if ok:
            cached_listar_usuarios.clear()
        return ok
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            st.error("Este nome de usuario ja existe.")
        else:
            st.error(f"Erro ao atualizar usuario: {e}")
        return False


def atualizar_senha(usuario_id, nova_senha):
    try:
        return db.atualizar_senha_portal(usuario_id, nova_senha)
    except Exception as e:
        st.error(f"Erro ao atualizar senha: {e}")
        return False


def excluir_usuario(usuario_id):
    try:
        ok = db.excluir_usuario(usuario_id)
        if ok:
            cached_listar_usuarios.clear()
        return ok
    except Exception as e:
        st.error(f"Erro ao excluir usuario: {e}")
        return False


def validar_link_powerbi(link):
    # Aceita relatorios do Power BI e tambem apps Streamlit (ex.: dashboards
    # internos publicados em *.streamlit.app), ambos embedados via iframe.
    padroes = [
        r"app\.powerbi\.com",
        r"powerbi\.com",
        r"view\?r=",
        r"embed\?",
        r"streamlit\.app",
        r"streamlit\.io",
        r"ts\.net",
    ]
    for padrao in padroes:
        if re.search(padrao, link, re.IGNORECASE):
            return True
    return False


def render_powerbi_fullscreen(relatorio):
    # Modo TELA CHEIA: remove margens e limite de largura do portal e estica o
    # iframe para ocupar quase toda a altura da janela.
    st.markdown(
        """
        <style>
            [data-testid="stMainBlockContainer"], .block-container {
                padding: 0.3rem 0.6rem 0 0.6rem !important;
                max-width: 100% !important;
            }
            .stApp iframe { height: 95vh !important; min-height: 95vh !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button(f"Voltar  ·  {relatorio['titulo']}", icon=":material/arrow_back:",
                 type="secondary"):
        if "relatorio_em_tela" in st.session_state:
            del st.session_state["relatorio_em_tela"]
        if "ocultar_sidebar_prev" in st.session_state:
            st.session_state["ocultar_sidebar"] = st.session_state["ocultar_sidebar_prev"]
            del st.session_state["ocultar_sidebar_prev"]
        st.rerun()

    link = relatorio["link_powerbi"]
    low = link.lower()
    # Painel Streamlit (cloud *.streamlit.app ou tunel *.ts.net) embeda via iframe.
    # 1) Acrescenta ?embed=true (sem isso o navegador bloqueia o iframe).
    # 2) Se houver DASH_TOKEN nos Secrets do Portal, injeta ?token=... para
    #    liberar o painel exposto na internet. O token vem SO dos Secrets do
    #    Portal — nunca fica salvo no banco (Supabase guarda a URL limpa).
    if "streamlit.app" in low or "ts.net" in low:
        if "embed=" not in low:
            link = link + ("&" if "?" in link else "?") + "embed=true"
        try:
            tok = str(st.secrets["DASH_TOKEN"])
        except Exception:  # noqa: BLE001  (sem token configurado)
            tok = ""
        if tok and "token=" not in link.lower():
            link = link + "&token=" + tok
    iframe_src = escape(link, quote=True)
    components.html(
        f"""
        <style>html,body{{margin:0;padding:0;height:100%;overflow:hidden;}}</style>
        <iframe
            src="{iframe_src}"
            style="border:0;width:100%;height:100vh;display:block;"
            allowfullscreen="true">
        </iframe>
        """,
        height=900,
        scrolling=False,
    )


apply_professional_theme()
if "ocultar_sidebar" not in st.session_state:
    st.session_state["ocultar_sidebar"] = False
apply_sidebar_visibility()

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    if os.path.exists("logo_janelas_1.png"):
        logo_path = "logo_janelas_1.png"
    else:
        logo_path = "logo.png"
    render_logo_centered(logo_path, 430, top_margin=52)

    st.markdown('<h1 class="portal-title">Portal Power BI</h1>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", border=False):
            st.subheader(":material/lock: Acesso ao sistema")
            username = st.text_input("Usuario", placeholder="Digite seu usuario")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            if st.form_submit_button("Entrar", icon=":material/login:",
                                     use_container_width=True, type="primary"):
                if username and senha:
                    usuario = verificar_login(username, senha)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.success(f"Bem-vindo, {usuario['username']}!")
                        st.rerun()
                    else:
                        st.error("Usuario ou senha incorretos.")
                else:
                    st.warning("Preencha todos os campos.")

        st.markdown("---")
        with st.expander("Informacoes de acesso"):
            st.write("Primeiro acesso: use as credenciais definidas pelo administrador.")
            st.write("Se for a primeira inicializacao, configure ADMIN_INITIAL_PASSWORD nos secrets.")
    st.stop()


usuario = st.session_state.usuario
is_admin = usuario["is_admin"]

with st.sidebar:
    sidebar_logo = "logo_sidebar.png" if os.path.exists("logo_sidebar.png") else "logo.png"
    render_logo(0, sidebar_logo, use_container_width=True)
    st.markdown('<h2 class="sidebar-brand">Grupo FRT</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-subtitle">Portal Power BI</p>', unsafe_allow_html=True)
    st.markdown("---")
    papel = "Administrador" if is_admin else "Usuário"
    icone_papel = "shield_person" if is_admin else "person"
    st.markdown(
        "<div style='display:flex;align-items:center;gap:.6rem;padding:.55rem .7rem;"
        "background:#F0F5EE;border:1px solid #E2E8E0;border-radius:12px'>"
        f"<span class='material-symbols-outlined' style='font-size:30px;color:#2E7D32'>{icone_papel}</span>"
        "<div style='line-height:1.15'>"
        f"<div style='font-weight:700;color:#1D2A22;font-size:.95rem'>{escape(usuario['username'])}</div>"
        f"<div style='color:#5B6B60;font-size:.74rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:.05em'>{papel}</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )
    if not is_admin:
        st.caption("Nível: " + NIVEL_LABELS.get(usuario.get("nivel_hierarquia"), "Operação"))
        st.caption("Áreas: " + ", ".join(usuario.get("categorias_permitidas") or []))

    st.markdown("---")
    if "menu_destino" in st.session_state:
        st.session_state["menu_atual"] = st.session_state["menu_destino"]
        del st.session_state["menu_destino"]

    if "menu_atual" not in st.session_state:
        st.session_state["menu_atual"] = MENU_DASHBOARD
    if "editar_relatorio" in st.session_state:
        st.session_state["menu_atual"] = MENU_NOVO_RELATORIO

    _nav = [
        (MENU_DASHBOARD, ":material/dashboard:", "Dashboard"),
        (MENU_NOVO_RELATORIO, ":material/add_chart:", "Novo relatório"),
    ]
    if is_admin:
        _nav.append((MENU_GERENCIAR_USUARIOS, ":material/group:", "Usuários"))
    _nav.append((MENU_MINHA_CONTA, ":material/manage_accounts:", "Minha conta"))

    for _valor, _icone, _rotulo in _nav:
        _ativo = st.session_state["menu_atual"] == _valor
        if st.button(_rotulo, icon=_icone, key=f"nav_{_valor}",
                     use_container_width=True,
                     type="primary" if _ativo else "secondary"):
            st.session_state["menu_atual"] = _valor
            st.rerun()
    menu = st.session_state["menu_atual"]

    st.markdown("---")
    if st.button("Sair", icon=":material/logout:", use_container_width=True, type="secondary"):
        st.session_state.usuario = None
        st.rerun()

# Em modo tela cheia (relatorio aberto) nao mostra cabecalho nem divisoria,
# para o relatorio ocupar a tela inteira.
_em_tela = menu == MENU_DASHBOARD and st.session_state.get("relatorio_em_tela")
if _em_tela:
    pass
elif menu == MENU_DASHBOARD:
    render_page_header("Dashboard de Relatórios")
elif menu == MENU_NOVO_RELATORIO:
    if "editar_relatorio" in st.session_state:
        render_page_header("Editar relatório")
    else:
        render_page_header("Adicionar novo relatório")
elif menu == MENU_GERENCIAR_USUARIOS:
    render_page_header("Gerenciamento de usuários")
else:
    render_page_header("Minha conta")

if not _em_tela:
    st.markdown("---")


if menu == MENU_DASHBOARD:
    relatorios = listar_relatorios(usuario)
    if st.session_state.get("relatorio_em_tela"):
        relatorio_tela = obter_relatorio_por_id(st.session_state["relatorio_em_tela"], usuario)
        if relatorio_tela is None:
            st.error("Relatorio nao encontrado ou voce nao tem permissao para acessa-lo.")
            del st.session_state["relatorio_em_tela"]
        else:
            render_powerbi_fullscreen(relatorio_tela)
            st.stop()

    if not relatorios:
        st.info("Nenhum relatorio disponivel nas suas categorias.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            categorias_disponiveis = sorted(list({r["categoria"] for r in relatorios}))
            filtro_cat = st.selectbox("Filtrar por categoria", ["Todas"] + categorias_disponiveis)
        with col2:
            buscar = st.text_input("Buscar relatorio", placeholder="Digite titulo ou descricao...")

        relatorios_filtrados = relatorios
        if filtro_cat != "Todas":
            relatorios_filtrados = [r for r in relatorios_filtrados if r["categoria"] == filtro_cat]
        if buscar:
            termo = buscar.lower()
            relatorios_filtrados = [
                r
                for r in relatorios_filtrados
                if termo in r["titulo"].lower() or (r["descricao"] and termo in r["descricao"].lower())
            ]

        st.markdown(
            "<div style='font-family:Poppins,Inter,sans-serif;font-weight:600;"
            "font-size:1.15rem;color:#14401E;margin:.2rem 0 .9rem'>"
            f"Relatórios disponíveis <span style='color:#5B6B60;font-weight:500'>"
            f"({len(relatorios_filtrados)})</span></div>",
            unsafe_allow_html=True,
        )
        if not relatorios_filtrados:
            st.info("Nenhum relatorio encontrado para o filtro/busca selecionados.")

        NCOLS = 3
        for inicio in range(0, len(relatorios_filtrados), NCOLS):
            linha = relatorios_filtrados[inicio:inicio + NCOLS]
            for col, relatorio in zip(st.columns(NCOLS), linha):
                with col:
                    with st.container(border=True):
                        desc = relatorio["descricao"] or "Sem descrição"
                        desc_short = (desc[:110] + "…") if len(desc) > 110 else desc
                        _nivel = relatorio.get("nivel_hierarquia", "operacao")
                        _is_gestao = _nivel == "gestao"
                        _nivel_bg = "#14401E" if _is_gestao else "#EAF0EE"
                        _nivel_fg = "#FFFFFF" if _is_gestao else "#5B6B60"
                        st.markdown(
                            "<span style='display:inline-block;background:#E6F0E2;"
                            "color:#14401E;font-size:.7rem;font-weight:700;letter-spacing:.04em;"
                            "text-transform:uppercase;padding:3px 10px;border-radius:999px'>"
                            f"{escape(relatorio['categoria'])}</span>"
                            f"<span style='display:inline-block;margin-left:.35rem;background:{_nivel_bg};"
                            f"color:{_nivel_fg};font-size:.7rem;font-weight:700;letter-spacing:.04em;"
                            "text-transform:uppercase;padding:3px 10px;border-radius:999px'>"
                            f"{escape(NIVEL_LABELS.get(_nivel, 'Operação'))}</span>"
                            "<div style='font-family:Poppins,Inter,sans-serif;font-weight:700;"
                            "font-size:1.02rem;color:#14401E;margin:.45rem 0 .2rem;line-height:1.25;"
                            "height:2.5em;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;"
                            "-webkit-box-orient:vertical'>"
                            f"{escape(relatorio['titulo'])}</div>"
                            "<div style='color:#5B6B60;font-size:.85rem;line-height:1.35;"
                            "height:2.7em;margin-bottom:.35rem;overflow:hidden;display:-webkit-box;"
                            "-webkit-line-clamp:2;-webkit-box-orient:vertical'>"
                            f"{escape(desc_short)}</div>"
                            "<div style='color:#93A096;font-size:.72rem;margin-bottom:.7rem;"
                            "display:flex;align-items:center;gap:.3rem'>"
                            "<span class='material-symbols-outlined' style='font-size:15px'>person</span>"
                            f"{escape(relatorio['criador'] or 'Sistema')}"
                            "<span style='margin:0 .25rem'>·</span>"
                            "<span class='material-symbols-outlined' style='font-size:15px'>event</span>"
                            f"{fmt_data(relatorio['criado_em'])}</div>",
                            unsafe_allow_html=True,
                        )
                        if st.button("Abrir", icon=":material/open_in_full:",
                                     key=f"open_{relatorio['id']}",
                                     use_container_width=True, type="primary"):
                            if "ocultar_sidebar_prev" not in st.session_state:
                                st.session_state["ocultar_sidebar_prev"] = st.session_state.get("ocultar_sidebar", False)
                            st.session_state["ocultar_sidebar"] = True
                            st.session_state["relatorio_em_tela"] = relatorio["id"]
                            st.rerun()

                        if is_admin or relatorio["criado_por"] == usuario["id"]:
                            ce, cd = st.columns(2)
                            with ce:
                                if st.button("Editar", icon=":material/edit:",
                                             key=f"edit_{relatorio['id']}",
                                             use_container_width=True):
                                    st.session_state["editar_relatorio"] = relatorio["id"]
                                    st.session_state["menu_destino"] = MENU_NOVO_RELATORIO
                                    st.rerun()
                            with cd:
                                if st.button("Excluir", icon=":material/delete:",
                                             key=f"del_{relatorio['id']}",
                                             use_container_width=True):
                                    if excluir_relatorio(relatorio["id"]):
                                        st.success("Relatorio excluido.")
                                        st.rerun()

elif menu == MENU_NOVO_RELATORIO:
    if "editar_relatorio" in st.session_state:
        relatorio = obter_relatorio_por_id(st.session_state["editar_relatorio"], usuario)
        modo_edicao = relatorio is not None
        if not modo_edicao:
            st.error("Relatorio nao encontrado ou voce nao tem permissao para edita-lo.")
            del st.session_state["editar_relatorio"]
            st.stop()
    else:
        relatorio = None
        modo_edicao = False

    opcoes_cat = categorias_disponiveis_para(usuario)
    opcoes_nivel = niveis_disponiveis_para(usuario)
    if modo_edicao:
        if relatorio["categoria"] not in opcoes_cat:
            opcoes_cat = [relatorio["categoria"]] + opcoes_cat
        if relatorio["nivel_hierarquia"] not in opcoes_nivel:
            opcoes_nivel = [relatorio["nivel_hierarquia"]] + opcoes_nivel

    # Chave do form varia por relatorio para nao reaproveitar valores de outro.
    _form_key = f"rel_form_{relatorio['id']}" if modo_edicao else "rel_form_novo"
    with st.form(_form_key, clear_on_submit=not modo_edicao):
        if modo_edicao:
            titulo = st.text_input("Titulo do relatorio *", value=relatorio["titulo"])
            link = st.text_area("Link do relatorio (Power BI ou Streamlit) *",
                                value=relatorio["link_powerbi"], height=120)
            descricao = st.text_area("Descricao", value=relatorio["descricao"] or "", height=100)
        else:
            titulo = st.text_input("Titulo do relatorio *", placeholder="Ex: Dashboard de Vendas")
            link = st.text_area("Link do relatorio (Power BI ou Streamlit) *", height=120)
            descricao = st.text_area("Descricao", height=100)

        col_cat, col_niv = st.columns(2)
        with col_cat:
            idx_cat = opcoes_cat.index(relatorio["categoria"]) if (
                modo_edicao and relatorio["categoria"] in opcoes_cat) else 0
            categoria = st.selectbox("Área de atuação *", opcoes_cat, index=idx_cat)
        with col_niv:
            if modo_edicao and relatorio["nivel_hierarquia"] in opcoes_nivel:
                idx_niv = opcoes_nivel.index(relatorio["nivel_hierarquia"])
            elif "operacao" in opcoes_nivel:
                idx_niv = opcoes_nivel.index("operacao")
            else:
                idx_niv = 0
            nivel = st.selectbox("Hierarquia *", opcoes_nivel,
                                 format_func=lambda n: NIVEL_LABELS[n], index=idx_niv)
        st.caption(
            "Hierarquia: relatórios de **Gestão** aparecem apenas para usuários de gestão; "
            "os de **Operação** aparecem para todos os níveis (sempre respeitando a área)."
        )

        st.markdown("---")
        if modo_edicao:
            col_salvar, col_cancelar = st.columns(2)
            with col_salvar:
                if st.form_submit_button("Salvar alterações", icon=":material/save:", type="primary", use_container_width=True):
                    if not titulo or not link:
                        st.error("Preencha os campos obrigatorios.")
                    elif not validar_link_powerbi(link):
                        st.error("Link invalido. Use um link do Power BI ou de um app Streamlit.")
                    else:
                        if atualizar_relatorio(relatorio["id"], titulo, link, descricao, categoria, nivel):
                            st.success("Relatorio atualizado com sucesso.")
                            del st.session_state["editar_relatorio"]
                            st.session_state["menu_destino"] = MENU_DASHBOARD
                            st.rerun()
            with col_cancelar:
                if st.form_submit_button("Cancelar", icon=":material/close:", type="secondary", use_container_width=True):
                    del st.session_state["editar_relatorio"]
                    st.session_state["menu_destino"] = MENU_DASHBOARD
                    st.rerun()
        else:
            if st.form_submit_button("Salvar relatório", icon=":material/save:", type="primary", use_container_width=True):
                if not titulo or not link:
                    st.error("Preencha os campos obrigatorios.")
                elif not validar_link_powerbi(link):
                    st.error("Link invalido. Use um link do Power BI ou de um app Streamlit.")
                else:
                    if criar_relatorio(titulo, link, descricao, categoria, usuario["id"], nivel):
                        st.success("Relatorio adicionado com sucesso.")
                        st.session_state["menu_destino"] = MENU_DASHBOARD
                        st.rerun()

elif menu == MENU_GERENCIAR_USUARIOS:
    if not is_admin:
        st.error("Acesso restrito. Apenas administradores podem gerenciar usuarios.")
        st.stop()

    usuarios_db = cached_listar_usuarios()
    modo_edicao = "editar_usuario_id" in st.session_state
    user_data = None
    if modo_edicao:
        user_data = next(
            (u for u in usuarios_db if u["id"] == st.session_state["editar_usuario_id"]), None
        )
        if user_data is None:
            st.warning("Usuário não encontrado (pode ter sido removido).")
            del st.session_state["editar_usuario_id"]
            st.rerun()

    # Chave estavel por usuario (ou por sessao de criacao): garante que ao trocar
    # de usuario os campos recarreguem os valores certos, sem estado preso.
    if modo_edicao:
        fid = f"edit{user_data['id']}"
        st.subheader(f":material/edit: Editando usuário: {user_data['username']}")
    else:
        fid = f"novo{st.session_state.get('novo_user_nonce', 0)}"
        st.subheader(":material/person_add: Criar novo usuário")

    st.markdown("**Dados de acesso**")
    novo_username = st.text_input(
        "Nome de usuário *",
        value=(user_data["username"] if modo_edicao else ""),
        key=f"u_username_{fid}",
    )
    if modo_edicao:
        alterar_senha = st.checkbox("Alterar senha?", key=f"u_chsenha_{fid}")
    else:
        alterar_senha = True
    if alterar_senha:
        c_s1, c_s2 = st.columns(2)
        nova_senha = c_s1.text_input("Senha *", type="password", key=f"u_senha_{fid}")
        confirmar_senha = c_s2.text_input("Confirmar senha *", type="password", key=f"u_csenha_{fid}")
    else:
        nova_senha = ""
        confirmar_senha = ""

    st.markdown("**Perfil e hierarquia**")
    col_perfil, col_nivel = st.columns(2)
    with col_perfil:
        perfil = st.radio(
            "Perfil",
            ["Usuário comum", "Administrador"],
            index=1 if (modo_edicao and user_data["is_admin"]) else 0,
            key=f"u_perfil_{fid}",
            help="Administrador enxerga todos os relatórios e gerencia usuários.",
        )
        user_is_admin = perfil == "Administrador"
    with col_nivel:
        if user_is_admin:
            st.radio("Nível hierárquico", ["Gestão"], index=0, disabled=True, key=f"u_niveladm_{fid}")
            nivel_sel = "gestao"
        else:
            nivel_atual = user_data["nivel_hierarquia"] if modo_edicao else "operacao"
            nivel_idx = (
                NIVEIS_HIERARQUIA.index(nivel_atual)
                if nivel_atual in NIVEIS_HIERARQUIA
                else NIVEIS_HIERARQUIA.index("operacao")
            )
            nivel_sel = st.radio(
                "Nível hierárquico",
                NIVEIS_HIERARQUIA,
                index=nivel_idx,
                format_func=lambda n: NIVEL_LABELS[n],
                key=f"u_nivel_{fid}",
                help="Gestão vê relatórios de gestão e de operação; Operação vê só os de operação.",
            )

    if user_is_admin:
        st.info("Administrador enxerga todos os relatórios — áreas e liberação individual não se aplicam.")
        areas_final = list(CATEGORIAS_PADRAO)
        indiv_sel = []
    else:
        st.markdown("**Filtro primário — áreas de atuação**")
        areas_default = [
            a for a in (user_data["categorias_permitidas"] if modo_edicao else ["GERAL"])
            if a in CATEGORIAS_PADRAO
        ]
        areas_sel = st.multiselect(
            "Áreas que o usuário pode acessar",
            CATEGORIAS_PADRAO,
            default=areas_default,
            key=f"u_areas_{fid}",
            help="O usuário só enxerga relatórios destas áreas.",
        )
        areas_final = areas_sel if areas_sel else ["GERAL"]

        st.markdown("**Filtro secundário — liberação individual**")
        rel_basico = cached_listar_relatorios_basico()
        rel_label = {
            r["id"]: f"{r['categoria']} · {NIVEL_LABELS[r['nivel_hierarquia']]} · {r['titulo']}"
            for r in rel_basico
        }
        rel_ids = [r["id"] for r in rel_basico]
        indiv_default = [
            i for i in (user_data["relatorios_permitidos"] if modo_edicao else []) if i in rel_label
        ]
        indiv_sel = st.multiselect(
            "Relatórios liberados individualmente",
            rel_ids,
            default=indiv_default,
            format_func=lambda i: rel_label.get(i, f"#{i}"),
            key=f"u_indiv_{fid}",
            help=("Deixe VAZIO para liberar todos os relatórios das áreas. Se marcar relatórios, "
                  "o usuário verá APENAS esses (sempre dentro das áreas e do nível permitidos)."),
        )

    st.markdown("")
    col_salvar, col_cancelar = st.columns(2)
    salvar = col_salvar.button(
        "Salvar alterações" if modo_edicao else "Criar usuário",
        icon=":material/save:", type="primary", use_container_width=True, key=f"u_salvar_{fid}",
    )
    cancelar = False
    if modo_edicao:
        cancelar = col_cancelar.button(
            "Cancelar", icon=":material/close:", type="secondary",
            use_container_width=True, key=f"u_cancelar_{fid}",
        )

    if cancelar:
        del st.session_state["editar_usuario_id"]
        st.rerun()

    if salvar:
        checar_senha = (not modo_edicao) or alterar_senha
        erro = None
        if not novo_username:
            erro = "Informe o nome de usuário."
        elif checar_senha:
            if not nova_senha or not confirmar_senha:
                erro = "Preencha e confirme a senha."
            elif nova_senha != confirmar_senha:
                erro = "As senhas não coincidem."
            elif len(nova_senha) < 6:
                erro = "A senha deve ter pelo menos 6 caracteres."

        if erro:
            st.error(erro)
        elif modo_edicao:
            ok = atualizar_usuario(
                user_data["id"], username=novo_username, is_admin=user_is_admin,
                nivel_hierarquia=nivel_sel, categorias_permitidas=areas_final,
                relatorios_permitidos=indiv_sel,
            )
            if ok:
                if alterar_senha:
                    atualizar_senha(user_data["id"], nova_senha)
                st.success("Usuário atualizado com sucesso.")
                del st.session_state["editar_usuario_id"]
                st.rerun()
        else:
            if criar_usuario(novo_username, nova_senha, user_is_admin, nivel_sel, areas_final, indiv_sel):
                st.success(f"Usuário {novo_username} criado com sucesso.")
                st.session_state["novo_user_nonce"] = st.session_state.get("novo_user_nonce", 0) + 1
                st.rerun()

    st.markdown("---")
    st.markdown("##### Usuários cadastrados")
    if not usuarios_db:
        st.info("Nenhum usuário cadastrado.")
    else:
        for user in usuarios_db:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"Usuário: {user['username']}")
                    st.write(f"Tipo: {'Administrador' if user['is_admin'] else 'Usuário comum'}")
                    if not user["is_admin"]:
                        st.write(f"Nível: {NIVEL_LABELS.get(user.get('nivel_hierarquia'), 'Operação')}")
                        st.write(f"Áreas: {', '.join(user['categorias_permitidas'][:6])}"
                                 + (f" … (+{len(user['categorias_permitidas']) - 6})"
                                    if len(user["categorias_permitidas"]) > 6 else ""))
                        qtd_indiv = len(user.get("relatorios_permitidos") or [])
                        if qtd_indiv:
                            st.write(f"Liberação individual: {qtd_indiv} relatório(s) — vê apenas esses")
                    st.write(f"Criado em: {fmt_data(user['criado_em'])}")
                with c2:
                    if st.button("Editar", icon=":material/edit:", key=f"edit_{user['id']}", type="secondary"):
                        st.session_state["editar_usuario_id"] = user["id"]
                        st.rerun()
                with c3:
                    if user["username"] != "admin":
                        if st.button("Excluir", icon=":material/delete:", key=f"delete_{user['id']}", type="secondary"):
                            if excluir_usuario(user["id"]):
                                if st.session_state.get("editar_usuario_id") == user["id"]:
                                    del st.session_state["editar_usuario_id"]
                                st.success(f"Usuário {user['username']} excluído.")
                                st.rerun()

elif menu == MENU_MINHA_CONTA:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(":material/person: Perfil")
        st.write(f"Usuário: {usuario['username']}")
        st.write(f"Tipo: {'Administrador' if is_admin else 'Usuário'}")
        if not is_admin:
            st.write(f"Nível hierárquico: {NIVEL_LABELS.get(usuario.get('nivel_hierarquia'), 'Operação')}")
            st.write("Áreas permitidas:")
            for cat in usuario["categorias_permitidas"]:
                st.write(f"- {cat}")
            qtd_indiv = len(usuario.get("relatorios_permitidos") or [])
            if qtd_indiv:
                st.caption(f"Acesso restrito a {qtd_indiv} relatório(s) liberado(s) individualmente.")

    with col2:
        st.subheader(":material/password: Alterar senha")
        with st.form("alterar_senha_form"):
            senha_atual = st.text_input("Senha atual *", type="password")
            nova_senha = st.text_input("Nova senha *", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
            if st.form_submit_button("Alterar senha", icon=":material/lock_reset:", type="primary"):
                if not all([senha_atual, nova_senha, confirmar_senha]):
                    st.error("Preencha todos os campos.")
                elif nova_senha != confirmar_senha:
                    st.error("As novas senhas nao coincidem.")
                elif len(nova_senha) < 6:
                    st.error("A nova senha deve ter pelo menos 6 caracteres.")
                else:
                    usuario_verificado = verificar_login(usuario["username"], senha_atual)
                    if not usuario_verificado:
                        st.error("Senha atual incorreta.")
                    else:
                        if atualizar_senha(usuario["id"], nova_senha):
                            st.success("Senha alterada com sucesso.")


st.markdown("---")
st.caption(f"Portal Power BI v3.0 (Supabase) | Usuário {usuario['username']}")
