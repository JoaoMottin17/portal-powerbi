import streamlit as st
from auth import AuthSystem
from database import Database
import re
import pandas as pd

# Inicializar sistemas
auth = AuthSystem()
db = Database()

# Verificar autenticação
auth.proteger_pagina()

# Obter usuário atual
usuario = auth.get_current_user()
is_admin = auth.is_admin()

# Sidebar - Menu
with st.sidebar:
    st.title(f"👤 {usuario['username']}")
    
    if is_admin:
        st.markdown("**⚙️ Administrador**")
    
    menu = st.selectbox(
        "Menu",
        ["📊 Dashboard", "➕ Novo Relatório", "👥 Gerenciar Usuários", "⚙️ Configurações"]
    )
    
    # Botão de logout
    if st.button("🚪 Sair", use_container_width=True):
        auth.logout()

# Função para validar link do Power BI
def validar_link_powerbi(link):
    """Validar se o link é do Power BI"""
    padroes = [
        r'app\.powerbi\.com',
        r'powerbi\.com',
        r'view\?r=',
        r'embed\?',
    ]
    
    for padrao in padroes:
        if re.search(padrao, link, re.IGNORECASE):
            return True
    
    return False

# Página: Dashboard
if menu == "📊 Dashboard":
    st.title("📊 Portal Power BI")
    
    # Buscar relatórios
    relatorios = db.listar_relatorios(ativos=True, usuario_id=usuario['id'])
    
    if not relatorios:
        st.info("Nenhum relatório disponível. Adicione um novo relatório!")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            categorias = list(set([r['categoria'] for r in relatorios]))
            categoria_filtro = st.selectbox("Filtrar por categoria", ["Todas"] + categorias)
        
        with col2:
            busca = st.text_input("🔍 Buscar relatório", placeholder="Título ou descrição...")
        
        # Aplicar filtros
        relatorios_filtrados = relatorios
        if categoria_filtro != "Todas":
            relatorios_filtrados = [r for r in relatorios_filtrados if r['categoria'] == categoria_filtro]
        
        if busca:
            busca_lower = busca.lower()
            relatorios_filtrados = [
                r for r in relatorios_filtrados 
                if busca_lower in r['titulo'].lower() or 
                (r['descricao'] and busca_lower in r['descricao'].lower())
            ]
        
        # Exibir relatórios
        st.subheader(f"Relatórios ({len(relatorios_filtrados)})")
        
        for relatorio in relatorios_filtrados:
            with st.expander(f"📈 {relatorio['titulo']} - *{relatorio['categoria']}*"):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.write(f"**Descrição:** {relatorio['descricao'] or 'Sem descrição'}")
                    st.write(f"**Criado por:** {relatorio['criador'] or 'Sistema'}")
                    st.write(f"**Data:** {relatorio['criado_em']}")
                    
                    if relatorio['tags']:
                        tags_html = " ".join([f"`{tag}`" for tag in relatorio['tags']])
                        st.markdown(f"**Tags:** {tags_html}")
                
                with col_b:
                    if st.button("Abrir", key=f"abrir_{relatorio['id']}", type="secondary"):
                        # Registrar acesso
                        db.registrar_acesso(usuario['id'], relatorio['id'])
                        
                        st.markdown("---")
                        st.subheader(relatorio['titulo'])
                        
                        # Preparar link para abrir em NOVA ABA
                        link = relatorio['link_powerbi']
                        
                        # Garantir que é link de "view" (não embed)
                        if "embed" in link:
                            link = link.replace("embed", "view")
                        
                        # Botão para abrir em nova aba
                        st.markdown(f"""
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{link}" target="_blank" style="text-decoration: none;">
                                <div style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    padding: 18px 35px;
                                    border-radius: 12px;
                                    font-size: 18px;
                                    font-weight: bold;
                                    cursor: pointer;
                                    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
                                    transition: all 0.3s ease;
                                    display: inline-flex;
                                    align-items: center;
                                    gap: 12px;
                                " 
                                onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 10px 20px rgba(0, 0, 0, 0.2)';"
                                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 12px rgba(0, 0, 0, 0.15)';"
                                >
                                <span style="font-size: 24px;">📊</span>
                                <span>ABRIR RELATÓRIO DO POWER BI</span>
                                <span style="font-size: 24px;">↗️</span>
                                </div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Link para cópia
                        with st.expander("📋 Copiar link manualmente"):
                            st.code(link, language="text")
                            if st.button("📋 Copiar link", key=f"copy_{relatorio['id']}"):
                                st.success("✅ Link copiado! Use Ctrl+V para colar.")
                
                # Botões de admin
                if is_admin or relatorio['criado_por'] == usuario['id']:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Editar", key=f"edit_{relatorio['id']}"):
                            st.session_state['editar_relatorio'] = relatorio['id']
                    with col_del:
                        if st.button("🗑️ Excluir", key=f"del_{relatorio['id']}"):
                            if db.excluir_relatorio(relatorio['id'])['success']:
                                st.success("Relatório excluído!")
                                st.rerun()
# Página: Novo Relatório
elif menu == "➕ Novo Relatório":
    st.title("➕ Adicionar Novo Relatório")
    
    with st.form("novo_relatorio_form"):
        titulo = st.text_input("Título do Relatório *", placeholder="Ex: Dashboard de Vendas")
        link = st.text_area("Link do Power BI *", 
                          placeholder="Cole aqui o link gerado pelo Power BI...",
                          height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            descricao = st.text_area("Descrição", placeholder="Descreva o relatório...")
        with col2:
            categoria = st.text_input("Categoria", value="Geral")
        
        tags = st.text_input("Tags (separadas por vírgula)", 
                           placeholder="vendas, marketing, financeiro")
        
        submitted = st.form_submit_button("Salvar Relatório", type="primary")
        
        if submitted:
            if not titulo or not link:
                st.error("Preencha os campos obrigatórios (*)!")
            elif not validar_link_powerbi(link):
                st.error("Link inválido! Certifique-se que é um link do Power BI.")
            else:
                # Processar tags
                tags_list = [tag.strip() for tag in tags.split(",")] if tags else []
                
                resultado = db.criar_relatorio(
                    titulo=titulo,
                    link_powerbi=link,
                    descricao=descricao,
                    categoria=categoria,
                    tags=tags_list if tags_list else None,
                    criado_por=usuario['id']
                )
                
                if resultado['success']:
                    st.success("✅ Relatório adicionado com sucesso!")
                    st.balloons()
                else:
                    st.error(f"Erro: {resultado['error']}")

# Página: Gerenciar Usuários (apenas admin)
elif menu == "👥 Gerenciar Usuários":
    if not is_admin:
        st.error("⚠️ Acesso restrito aos administradores!")
        st.stop()
    
    st.title("👥 Gerenciamento de Usuários")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["Listar Usuários", "Criar Usuário", "Estatísticas"])
    
    # Tab 1: Listar Usuários
    with tab1:
        usuarios = db.listar_usuarios()
        
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Converter para DataFrame para melhor visualização
            df_usuarios = pd.DataFrame(usuarios)
            df_usuarios['is_admin'] = df_usuarios['is_admin'].map({1: 'Sim', 0: 'Não'})
            df_usuarios['ativo'] = df_usuarios['ativo'].map({1: '✅ Ativo', 0: '❌ Inativo'})
            
            st.dataframe(
                df_usuarios[['id', 'username', 'email', 'is_admin', 'criado_em', 'ativo']],
                use_container_width=True,
                hide_index=True
            )
            
            # Editar usuário
            st.subheader("Editar Usuário")
            usuario_id = st.number_input("ID do usuário para editar", min_value=1, step=1)
            
            if usuario_id:
                usuario_edit = next((u for u in usuarios if u['id'] == usuario_id), None)
                
                if usuario_edit:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        novo_username = st.text_input("Usuário", value=usuario_edit['username'])
                        novo_email = st.text_input("Email", value=usuario_edit['email'])
                    
                    with col2:
                        nova_senha = st.text_input("Nova senha (deixe em branco para manter)", type="password")
                        is_admin_edit = st.checkbox("Administrador", value=bool(usuario_edit['is_admin']))
                        ativo = st.checkbox("Ativo", value=bool(usuario_edit['ativo']))
                    
                    if st.button("Atualizar Usuário", type="primary"):
                        updates = {
                            'username': novo_username,
                            'email': novo_email,
                            'is_admin': is_admin_edit,
                            'ativo': ativo
                        }
                        
                        if nova_senha:
                            updates['password'] = nova_senha
                        
                        resultado = db.atualizar_usuario(usuario_id, **updates)
                        
                        if resultado['success']:
                            st.success("Usuário atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro: {resultado['error']}")
                else:
                    st.warning("Usuário não encontrado!")
    
    # Tab 2: Criar Usuário
    with tab2:
        st.subheader("Criar Novo Usuário")
        
        with st.form("criar_usuario_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                novo_username = st.text_input("Nome de usuário *")
                novo_email = st.text_input("Email *")
            
            with col2:
                nova_senha = st.text_input("Senha *", type="password")
                confirmar_senha = st.text_input("Confirmar senha *", type="password")
            
            is_admin_novo = st.checkbox("É administrador?")
            
            submitted = st.form_submit_button("Criar Usuário", type="primary")
            
            if submitted:
                if not all([novo_username, novo_email, nova_senha, confirmar_senha]):
                    st.error("Preencha todos os campos obrigatórios!")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem!")
                elif len(nova_senha) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres!")
                else:
                    resultado = db.criar_usuario(
                        username=novo_username,
                        email=novo_email,
                        password=nova_senha,
                        is_admin=is_admin_novo
                    )
                    
                    if resultado['success']:
                        st.success(f"✅ Usuário '{novo_username}' criado com ID: {resultado['user_id']}")
                    else:
                        st.error(f"Erro: {resultado['error']}")
    
    # Tab 3: Estatísticas
    with tab3:
        st.subheader("📈 Estatísticas do Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Usuários", len([u for u in usuarios if u['ativo']]))
        
        with col2:
            relatorios = db.listar_relatorios(ativos=True)
            st.metric("Total de Relatórios", len(relatorios))
        
        with col3:
            admins = len([u for u in usuarios if u['is_admin'] and u['ativo']])
            st.metric("Administradores", admins)

# Página: Configurações
elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    tab1, tab2 = st.tabs(["Minha Conta", "Sistema"])
    
    # Minha Conta
    with tab1:
        st.subheader("Minha Conta")
        
        with st.form("minha_conta_form"):
            st.write(f"**Usuário atual:** {usuario['username']}")
            
            nova_senha = st.text_input("Nova senha", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password")
            
            if st.form_submit_button("Alterar Senha", type="primary"):
                if nova_senha and confirmar_senha:
                    if nova_senha == confirmar_senha:
                        if len(nova_senha) >= 6:
                            resultado = db.atualizar_usuario(usuario['id'], password=nova_senha)
                            if resultado['success']:
                                st.success("✅ Senha alterada com sucesso!")
                            else:
                                st.error("Erro ao alterar senha!")
                        else:
                            st.error("A senha deve ter pelo menos 6 caracteres!")
                    else:
                        st.error("As senhas não coincidem!")
                else:
                    st.error("Preencha ambos os campos de senha!")
    
    # Sistema
    with tab2:
        st.subheader("Configurações do Sistema")
        
        if is_admin:
            # Backup do banco de dados
            if st.button("💾 Fazer Backup do Banco de Dados"):
                import shutil
                import datetime
                
                try:
                    data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = f"portal_backup_{data_hora}.db"
                    shutil.copy2("portal.db", backup_file)
                    st.success(f"✅ Backup criado: `{backup_file}`")
                    st.download_button(
                        label="📥 Baixar Backup",
                        data=open(backup_file, 'rb'),
                        file_name=backup_file,
                        mime="application/x-sqlite3"
                    )
                except Exception as e:
                    st.error(f"Erro ao criar backup: {e}")
            
            # Restaurar backup
            st.markdown("---")
            st.subheader("Restaurar Backup")
            
            uploaded_file = st.file_uploader("Selecione um arquivo .db para restaurar", type=['db'])
            
            if uploaded_file and st.button("🔄 Restaurar Backup", type="secondary"):
                try:
                    with open("portal_restore.db", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.warning("⚠️ **ATENÇÃO:** Esta ação irá substituir o banco atual!")
                    
                    if st.button("✅ Confirmar Restauração"):
                        import os
                        os.replace("portal_restore.db", "portal.db")
                        st.success("✅ Banco de dados restaurado com sucesso!")
                        st.info("Recarregue a página para aplicar as alterações.")
                except Exception as e:
                    st.error(f"Erro ao restaurar: {e}")
        else:
            st.info("Apenas administradores podem acessar estas configurações.")

# Rodapé
st.markdown("---")
st.caption(f"Portal Power BI v1.0 | Usuário: {usuario['username']} | paineis-grupofrt.streamlit.app | SQLite Database")