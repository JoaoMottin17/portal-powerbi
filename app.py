import os
import re
import base64

import streamlit as st
from database import Database


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

MENU_DASHBOARD = "📊 Dashboard"
MENU_NOVO_RELATORIO = "➕ Novo Relatorio"
MENU_GERENCIAR_USUARIOS = "👥 Gerenciar Usuarios"
MENU_MINHA_CONTA = "⚙️ Minha Conta"


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
    elif os.path.exists("logo_janelas.png"):
        janelas_logo = "logo_janelas.png"
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
            .stApp {
                background: #f7f8fa;
            }
            .block-container {
                padding-top: 1.2rem;
            }
            [data-testid="stSidebar"] {
                background: #eef1f5;
            }
            .portal-kicker {
                margin: 0;
                text-align: center;
                color: #5f6b7a;
                font-size: 0.95rem;
                font-weight: 500;
            }
            .portal-title {
                margin: 0.2rem 0 0.8rem 0;
                color: #1d2733;
                font-size: 2.6rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }
            .sidebar-brand {
                margin: -0.35rem 0 0.05rem 0;
                text-align: center;
                color: #0f365f;
                font-size: 2.2rem;
                font-weight: 700;
                letter-spacing: -0.01em;
            }
            .sidebar-subtitle {
                margin: 0 0 0.1rem 0;
                text-align: center;
                color: #6b7280;
                font-size: 0.95rem;
                font-weight: 500;
            }
            [data-testid="stSidebar"] [data-testid="stImage"] {
                margin-bottom: 0 !important;
            }
            .sidebar-user {
                margin: 0;
                color: #1f2937;
                font-size: 1.02rem;
                font-weight: 600;
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #0f7b3a 0%, #2fa84f 100%);
                border: none;
                color: #ffffff;
                font-weight: 700;
            }
            .stButton > button[kind="primary"]:hover {
                filter: brightness(0.96);
            }
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


def render_page_header(title_text: str):
    if os.path.exists("logo_janelas_1.png"):
        logo_path = "logo_janelas_1.png"
    elif os.path.exists("logo_janelas.png"):
        logo_path = "logo_janelas.png"
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
    padroes = [
        r"app\.powerbi\.com",
        r"powerbi\.com",
        r"view\?r=",
        r"embed\?",
    ]
    for padrao in padroes:
        if re.search(padrao, link, re.IGNORECASE):
            return True
    return False


init_db()
apply_professional_theme()

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    if os.path.exists("logo_janelas_1.png"):
        logo_path = "logo_janelas_1.png"
    elif os.path.exists("logo_janelas.png"):
        logo_path = "logo_janelas.png"
    else:
        logo_path = "logo.png"
    render_logo_centered(logo_path, 430, top_margin=52)

    st.markdown('<h1 class="portal-title">📈 Portal Power BI</h1>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", border=False):
            st.subheader("🔐 Acesso ao sistema")
            username = st.text_input("Usuario", placeholder="Digite seu usuario")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            if st.form_submit_button("🚀 Entrar", use_container_width=True, type="primary"):
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
    st.markdown(f'<p class="sidebar-user">Usuario: {usuario["username"]}</p>', unsafe_allow_html=True)
    if is_admin:
        st.success("Administrador")
    else:
        cats = usuario["categorias_permitidas"]
        st.info(f"Categorias: {', '.join(cats)}")

    st.markdown("---")
    menu = st.radio(
        "Menu principal",
        [MENU_DASHBOARD, MENU_NOVO_RELATORIO, MENU_GERENCIAR_USUARIOS, MENU_MINHA_CONTA],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if st.button("🚪 Sair", use_container_width=True, type="secondary"):
        st.session_state.usuario = None
        st.rerun()

if menu == MENU_DASHBOARD:
    render_page_header("📊 Dashboard de Relatorios")
elif menu == MENU_NOVO_RELATORIO:
    if "editar_relatorio" in st.session_state:
        render_page_header("✏️ Editar relatorio")
    else:
        render_page_header("➕ Adicionar novo relatorio")
elif menu == MENU_GERENCIAR_USUARIOS:
    render_page_header("👥 Gerenciamento de usuarios")
else:
    render_page_header("⚙️ Minha conta")

st.markdown("---")


if menu == MENU_DASHBOARD:
    relatorios = listar_relatorios(usuario)
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

        st.subheader(f"📋 Relatorios disponiveis ({len(relatorios_filtrados)})")
        for relatorio in relatorios_filtrados:
            with st.expander(f"{relatorio['titulo']} - {relatorio['categoria']}"):
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"Descricao: {relatorio['descricao'] or 'Sem descricao'}")
                    st.write(f"Criado por: {relatorio['criador'] or 'Sistema'}")
                    st.write(f"Criado em: {relatorio['criado_em']}")
                    if relatorio["atualizado_em"] and relatorio["atualizado_em"] != relatorio["criado_em"]:
                        st.write(f"Atualizado em: {relatorio['atualizado_em']}")

                with col_btn:
                    link = relatorio["link_powerbi"]
                    if "embed" in link:
                        link = link.replace("embed", "view")
                    st.link_button("📊 Abrir Power BI", link, use_container_width=True)

                st.markdown("---")
                st.code(link, language="text")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("📋 Copiar link", key=f"copy_{relatorio['id']}"):
                        st.success("Link copiado.")
                if is_admin or relatorio["criado_por"] == usuario["id"]:
                    with c2:
                        if st.button("✏️ Editar", key=f"edit_{relatorio['id']}"):
                            st.session_state["editar_relatorio"] = relatorio["id"]
                            st.rerun()
                    with c3:
                        if st.button("🗑️ Excluir", key=f"del_{relatorio['id']}"):
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
            link = st.text_area("Link do Power BI *", value=relatorio["link_powerbi"], height=120)
            descricao = st.text_area("Descricao", value=relatorio["descricao"] or "", height=100)
            idx = CATEGORIAS_PADRAO.index(relatorio["categoria"]) if relatorio["categoria"] in CATEGORIAS_PADRAO else 0
            categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO, index=idx)
        else:
            titulo = st.text_input("Titulo do relatorio *", placeholder="Ex: Dashboard de Vendas")
            link = st.text_area("Link do Power BI *", height=120)
            descricao = st.text_area("Descricao", height=100)
            categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO)

        st.markdown("---")
        if modo_edicao:
            col_salvar, col_cancelar = st.columns(2)
            with col_salvar:
                if st.form_submit_button("💾 Salvar alteracoes", type="primary", use_container_width=True):
                    if not titulo or not link:
                        st.error("Preencha os campos obrigatorios.")
                    elif not validar_link_powerbi(link):
                        st.error("Link invalido. Use um link do Power BI.")
                    else:
                        if atualizar_relatorio(relatorio["id"], titulo, link, descricao, categoria):
                            st.success("Relatorio atualizado com sucesso.")
                            del st.session_state["editar_relatorio"]
                            st.rerun()
            with col_cancelar:
                if st.form_submit_button("❌ Cancelar", type="secondary", use_container_width=True):
                    del st.session_state["editar_relatorio"]
                    st.rerun()
        else:
            if st.form_submit_button("💾 Salvar relatorio", type="primary", use_container_width=True):
                if not titulo or not link:
                    st.error("Preencha os campos obrigatorios.")
                elif not validar_link_powerbi(link):
                    st.error("Link invalido. Use um link do Power BI.")
                else:
                    if criar_relatorio(titulo, link, descricao, categoria, usuario["id"]):
                        st.success("Relatorio adicionado com sucesso.")
                        st.rerun()

elif menu == MENU_GERENCIAR_USUARIOS:
    if not is_admin:
        st.error("Acesso restrito. Apenas administradores podem gerenciar usuarios.")
        st.stop()

    if "editar_usuario_id" in st.session_state:
        tab1, tab2 = st.tabs(["✏️ Editar usuario", "📋 Lista de usuarios"])
    else:
        tab1, tab2 = st.tabs(["👤 Criar novo usuario", "📋 Lista de usuarios"])

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
                        st.write(f"Criado em: {user['criado_em']}")
                    with c2:
                        if st.button("✏️ Editar", key=f"edit_{user['id']}", type="secondary"):
                            st.session_state["editar_usuario_id"] = user["id"]
                            st.rerun()
                    with c3:
                        if user["username"] != "admin":
                            if st.button("🗑️ Excluir", key=f"delete_{user['id']}", type="secondary"):
                                if excluir_usuario(user["id"]):
                                    st.success(f"Usuario {user['username']} excluido.")
                                    st.rerun()

elif menu == MENU_MINHA_CONTA:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("👤 Perfil")
        st.write(f"Usuario: {usuario['username']}")
        st.write(f"Tipo: {'Administrador' if is_admin else 'Usuario'}")
        if not is_admin:
            st.write("Categorias permitidas:")
            for cat in usuario["categorias_permitidas"]:
                st.write(f"- {cat}")

    with col2:
        st.subheader("🔐 Alterar senha")
        with st.form("alterar_senha_form"):
            senha_atual = st.text_input("Senha atual *", type="password")
            nova_senha = st.text_input("Nova senha *", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
            if st.form_submit_button("🔄 Alterar senha", type="primary"):
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
