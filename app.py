import os
import re
import base64
from html import escape
from datetime import datetime, timedelta, timezone

import streamlit as st
import streamlit.components.v1 as components
from database import Database


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


st.set_page_config(
    page_title="Portal Power BI - Grupo FRT",
    page_icon=":bar_chart:",
    layout="wide",
)


CATEGORIAS_PADRAO = [
    "Geral",
    "Vendas",
    "Marketing",
    "Financeiro",
    "RH",
    "Operacoes",
    "Logistica",
    "Suprimentos",
    "Operacional",
]

MENU_DASHBOARD = "Dashboard"
MENU_NOVO_RELATORIO = "Novo relatorio"
MENU_GERENCIAR_USUARIOS = "Usuarios"
MENU_MINHA_CONTA = "Minha conta"


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


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


def init_db():
    try:
        db.init_database()
    except Exception as e:
        st.error(
            "Erro ao acessar tabelas no Supabase. "
            "Crie a estrutura com o arquivo supabase_schema.sql."
        )
        st.exception(e)
        st.stop()


def verificar_login(username: str, senha: str):
    return db.autenticar_usuario(username, senha)


def listar_relatorios(usuario):
    return db.listar_relatorios_usuario(usuario)


def obter_relatorio_por_id(relatorio_id: int):
    return db.obter_relatorio_por_id(relatorio_id)


def criar_relatorio(titulo, link_powerbi, descricao, categoria, criado_por):
    try:
        return db.criar_relatorio(titulo, link_powerbi, descricao, categoria, criado_por)
    except Exception as e:
        st.error(f"Erro ao criar relatorio: {e}")
        return False


def atualizar_relatorio(relatorio_id, titulo, link_powerbi, descricao, categoria):
    try:
        return db.atualizar_relatorio(relatorio_id, titulo, link_powerbi, descricao, categoria)
    except Exception as e:
        st.error(f"Erro ao atualizar relatorio: {e}")
        return False


def excluir_relatorio(relatorio_id):
    try:
        return db.excluir_relatorio(relatorio_id)
    except Exception as e:
        st.error(f"Erro ao excluir relatorio: {e}")
        return False


def listar_usuarios():
    return db.listar_usuarios()


def obter_usuario_por_id(usuario_id):
    return db.obter_usuario_por_id(usuario_id)


def criar_usuario(username, senha, is_admin=False, categorias_permitidas=None):
    try:
        return db.criar_usuario_portal(username, senha, is_admin, categorias_permitidas)
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            st.error("Este nome de usuario ja existe.")
        else:
            st.error(f"Erro ao criar usuario: {e}")
        return False


def atualizar_usuario(usuario_id, username=None, is_admin=None, categorias_permitidas=None):
    try:
        return db.atualizar_usuario_portal(usuario_id, username, is_admin, categorias_permitidas)
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
        return db.excluir_usuario(usuario_id)
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


init_db()
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
        st.caption("Categorias: " + ", ".join(usuario["categorias_permitidas"]))

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
        relatorio_tela = obter_relatorio_por_id(st.session_state["relatorio_em_tela"])
        if relatorio_tela is None:
            st.error("Relatorio selecionado nao foi encontrado.")
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
                        st.markdown(
                            "<span style='display:inline-block;background:#E6F0E2;"
                            "color:#14401E;font-size:.7rem;font-weight:700;letter-spacing:.04em;"
                            "text-transform:uppercase;padding:3px 10px;border-radius:999px'>"
                            f"{escape(relatorio['categoria'])}</span>"
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
        relatorio = obter_relatorio_por_id(st.session_state["editar_relatorio"])
        modo_edicao = relatorio is not None
    else:
        relatorio = None
        modo_edicao = False

    with st.form("novo_relatorio_form", clear_on_submit=not modo_edicao):
        if modo_edicao:
            titulo = st.text_input("Titulo do relatorio *", value=relatorio["titulo"])
            link = st.text_area("Link do relatorio (Power BI ou Streamlit) *", value=relatorio["link_powerbi"], height=120)
            descricao = st.text_area("Descricao", value=relatorio["descricao"] or "", height=100)
            idx = CATEGORIAS_PADRAO.index(relatorio["categoria"]) if relatorio["categoria"] in CATEGORIAS_PADRAO else 0
            categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO, index=idx)
        else:
            titulo = st.text_input("Titulo do relatorio *", placeholder="Ex: Dashboard de Vendas")
            link = st.text_area("Link do relatorio (Power BI ou Streamlit) *", height=120)
            descricao = st.text_area("Descricao", height=100)
            categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO)

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
                        if atualizar_relatorio(relatorio["id"], titulo, link, descricao, categoria):
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
                    if criar_relatorio(titulo, link, descricao, categoria, usuario["id"]):
                        st.success("Relatorio adicionado com sucesso.")
                        st.session_state["menu_destino"] = MENU_DASHBOARD
                        st.rerun()

elif menu == MENU_GERENCIAR_USUARIOS:
    if not is_admin:
        st.error("Acesso restrito. Apenas administradores podem gerenciar usuarios.")
        st.stop()

    if "editar_usuario_id" in st.session_state:
        tab1, tab2 = st.tabs([":material/edit: Editar usuário", ":material/list: Lista de usuários"])
    else:
        tab1, tab2 = st.tabs([":material/person_add: Criar novo usuário", ":material/list: Lista de usuários"])

    with tab1:
        if "editar_usuario_id" in st.session_state:
            user_data = obter_usuario_por_id(st.session_state["editar_usuario_id"])
            modo_edicao = True
        else:
            user_data = None
            modo_edicao = False

        with st.form("criar_editar_usuario_form"):
            if modo_edicao:
                novo_username = st.text_input("Nome de usuario *", value=user_data["username"])
                alterar_senha = st.checkbox("Alterar senha?")
                if alterar_senha:
                    nova_senha = st.text_input("Nova senha *", type="password")
                    confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
                else:
                    nova_senha = ""
                    confirmar_senha = ""
            else:
                novo_username = st.text_input("Nome de usuario *")
                nova_senha = st.text_input("Senha *", type="password")
                confirmar_senha = st.text_input("Confirmar senha *", type="password")

            user_is_admin = st.checkbox("E administrador?", value=user_data["is_admin"] if modo_edicao else False)
            categorias_selecionadas = []
            if not user_is_admin:
                st.markdown("### Categorias permitidas")
                if modo_edicao and user_data:
                    categorias_selecionadas = list(user_data["categorias_permitidas"])

                colunas = st.columns(3)
                selecionadas = set(categorias_selecionadas)
                for i, categoria in enumerate(CATEGORIAS_PADRAO):
                    with colunas[i % 3]:
                        if st.checkbox(categoria, value=categoria in selecionadas, key=f"cat_{categoria}"):
                            selecionadas.add(categoria)
                        else:
                            selecionadas.discard(categoria)
                categorias_selecionadas = sorted(list(selecionadas))
                if not categorias_selecionadas:
                    categorias_selecionadas = ["Geral"]

            col_salvar, col_cancelar = st.columns(2)
            with col_salvar:
                btn_text = "Salvar alteracoes" if modo_edicao else "Criar usuario"
                if st.form_submit_button(btn_text, type="primary", use_container_width=True):
                    if modo_edicao:
                        if alterar_senha and nova_senha and confirmar_senha:
                            if nova_senha != confirmar_senha:
                                st.error("As senhas nao coincidem.")
                            elif len(nova_senha) < 6:
                                st.error("A senha deve ter pelo menos 6 caracteres.")
                            else:
                                if atualizar_senha(user_data["id"], nova_senha):
                                    st.success("Senha atualizada.")

                        ok = atualizar_usuario(
                            user_data["id"],
                            username=novo_username,
                            is_admin=user_is_admin,
                            categorias_permitidas=categorias_selecionadas if not user_is_admin else CATEGORIAS_PADRAO,
                        )
                        if ok:
                            st.success("Usuario atualizado com sucesso.")
                            if "editar_usuario_id" in st.session_state:
                                del st.session_state["editar_usuario_id"]
                            st.rerun()
                    else:
                        if not all([novo_username, nova_senha, confirmar_senha]):
                            st.error("Preencha todos os campos.")
                        elif nova_senha != confirmar_senha:
                            st.error("As senhas nao coincidem.")
                        elif len(nova_senha) < 6:
                            st.error("A senha deve ter pelo menos 6 caracteres.")
                        else:
                            if criar_usuario(
                                novo_username,
                                nova_senha,
                                user_is_admin,
                                categorias_selecionadas if not user_is_admin else None,
                            ):
                                st.success(f"Usuario {novo_username} criado com sucesso.")
                                st.rerun()

            with col_cancelar:
                if modo_edicao and st.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                    if "editar_usuario_id" in st.session_state:
                        del st.session_state["editar_usuario_id"]
                    st.rerun()

    with tab2:
        usuarios_db = listar_usuarios()
        if not usuarios_db:
            st.info("Nenhum usuario cadastrado.")
        else:
            for user in usuarios_db:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(f"Usuario: {user['username']}")
                        st.write(f"Tipo: {'Administrador' if user['is_admin'] else 'Usuario comum'}")
                        if not user["is_admin"]:
                            st.write(f"Categorias: {', '.join(user['categorias_permitidas'][:5])}")
                            if len(user["categorias_permitidas"]) > 5:
                                st.write(f"... e mais {len(user['categorias_permitidas']) - 5}")
                        st.write(f"Criado em: {fmt_data(user['criado_em'])}")
                    with c2:
                        if st.button("Editar", icon=":material/edit:", key=f"edit_{user['id']}", type="secondary"):
                            st.session_state["editar_usuario_id"] = user["id"]
                            st.rerun()
                    with c3:
                        if user["username"] != "admin":
                            if st.button("Excluir", icon=":material/delete:", key=f"delete_{user['id']}", type="secondary"):
                                if excluir_usuario(user["id"]):
                                    st.success(f"Usuario {user['username']} excluido.")
                                    st.rerun()

elif menu == MENU_MINHA_CONTA:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(":material/person: Perfil")
        st.write(f"Usuario: {usuario['username']}")
        st.write(f"Tipo: {'Administrador' if is_admin else 'Usuario'}")
        if not is_admin:
            st.write("Categorias permitidas:")
            for cat in usuario["categorias_permitidas"]:
                st.write(f"- {cat}")

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
st.caption(f"Portal Power BI v2.0 (Supabase) | Usuario {usuario['username']}")
