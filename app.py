import os
import re

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


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


def render_logo(width: int):
    if os.path.exists("logo.png"):
        st.image("logo.png", width=width)


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

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    col_logo, col_titulo = st.columns([1, 3])
    with col_logo:
        render_logo(260)
    with col_titulo:
        st.title("Portal Power BI")
        st.subheader("Grupo FRT")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", border=False):
            st.subheader("Acesso ao sistema")
            username = st.text_input("Usuario", placeholder="Digite seu usuario")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            if st.form_submit_button("Entrar", use_container_width=True):
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
    render_logo(160)
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:20px;">
            <h2 style="color:#0E2C4D;">Grupo FRT</h2>
            <p style="color:#666;font-size:14px;">Portal Power BI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.write(f"Usuario: {usuario['username']}")
    if is_admin:
        st.success("Administrador")
    else:
        cats = usuario["categorias_permitidas"]
        st.info(f"Categorias: {', '.join(cats)}")

    st.markdown("---")
    menu = st.radio(
        "Menu principal",
        ["Dashboard", "Novo Relatorio", "Gerenciar Usuarios", "Minha Conta"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if st.button("Sair", use_container_width=True, type="secondary"):
        st.session_state.usuario = None
        st.rerun()


col_logo_header, col_title_header = st.columns([1, 4])
with col_logo_header:
    render_logo(90)
with col_title_header:
    if menu == "Dashboard":
        st.title("Dashboard de Relatorios")
    elif menu == "Novo Relatorio":
        if "editar_relatorio" in st.session_state:
            st.title("Editar relatorio")
        else:
            st.title("Adicionar novo relatorio")
    elif menu == "Gerenciar Usuarios":
        st.title("Gerenciamento de usuarios")
    else:
        st.title("Minha conta")

st.markdown("---")


if menu == "Dashboard":
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

        st.subheader(f"Relatorios disponiveis ({len(relatorios_filtrados)})")
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
                    st.link_button("Abrir Power BI", link, use_container_width=True)

                st.markdown("---")
                st.code(link, language="text")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("Copiar link", key=f"copy_{relatorio['id']}"):
                        st.success("Link copiado.")
                if is_admin or relatorio["criado_por"] == usuario["id"]:
                    with c2:
                        if st.button("Editar", key=f"edit_{relatorio['id']}"):
                            st.session_state["editar_relatorio"] = relatorio["id"]
                            st.rerun()
                    with c3:
                        if st.button("Excluir", key=f"del_{relatorio['id']}"):
                            if excluir_relatorio(relatorio["id"]):
                                st.success("Relatorio excluido.")
                                st.rerun()

elif menu == "Novo Relatorio":
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
                if st.form_submit_button("Salvar alteracoes", type="primary", use_container_width=True):
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
                if st.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                    del st.session_state["editar_relatorio"]
                    st.rerun()
        else:
            if st.form_submit_button("Salvar relatorio", type="primary", use_container_width=True):
                if not titulo or not link:
                    st.error("Preencha os campos obrigatorios.")
                elif not validar_link_powerbi(link):
                    st.error("Link invalido. Use um link do Power BI.")
                else:
                    if criar_relatorio(titulo, link, descricao, categoria, usuario["id"]):
                        st.success("Relatorio adicionado com sucesso.")
                        st.rerun()

elif menu == "Gerenciar Usuarios":
    if not is_admin:
        st.error("Acesso restrito. Apenas administradores podem gerenciar usuarios.")
        st.stop()

    if "editar_usuario_id" in st.session_state:
        tab1, tab2 = st.tabs(["Editar usuario", "Lista de usuarios"])
    else:
        tab1, tab2 = st.tabs(["Criar novo usuario", "Lista de usuarios"])

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
                        if st.button("Editar", key=f"edit_{user['id']}", type="secondary"):
                            st.session_state["editar_usuario_id"] = user["id"]
                            st.rerun()
                    with c3:
                        if user["username"] != "admin":
                            if st.button("Excluir", key=f"delete_{user['id']}", type="secondary"):
                                if excluir_usuario(user["id"]):
                                    st.success(f"Usuario {user['username']} excluido.")
                                    st.rerun()

elif menu == "Minha Conta":
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Perfil")
        st.write(f"Usuario: {usuario['username']}")
        st.write(f"Tipo: {'Administrador' if is_admin else 'Usuario'}")
        if not is_admin:
            st.write("Categorias permitidas:")
            for cat in usuario["categorias_permitidas"]:
                st.write(f"- {cat}")

    with col2:
        st.subheader("Alterar senha")
        with st.form("alterar_senha_form"):
            senha_atual = st.text_input("Senha atual *", type="password")
            nova_senha = st.text_input("Nova senha *", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
            if st.form_submit_button("Alterar senha", type="primary"):
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
