import streamlit as st
import sqlite3
import hashlib
import re

# ========== CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Portal Power BI - Grupo FRT",
    page_icon="📊",
    layout="wide"
)

# ========== BANCO DE DADOS ==========
def init_db():
    """Inicializar banco de dados"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    # Usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Relatórios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relatorios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        link_powerbi TEXT NOT NULL,
        descricao TEXT,
        categoria TEXT DEFAULT 'Geral',
        criado_por INTEGER,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (criado_por) REFERENCES usuarios(id)
    )''')
    
    # Verificar se admin existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        # SENHA CORRETA: admin123
        password_hash = hashlib.sha256(b"admin123_salt_grupofrt").hexdigest()
        cursor.execute('''
        INSERT INTO usuarios (username, password_hash, is_admin)
        VALUES (?, ?, ?)''', ('admin', password_hash, 1))
    
    conn.commit()
    conn.close()

# ========== FUNÇÕES AUXILIARES ==========
def hash_senha(senha):
    """Hash para senhas - DEVE SER IGUAL AO USADO NA CRIAÇÃO DO ADMIN"""
    return hashlib.sha256(f"{senha}_salt_grupofrt".encode()).hexdigest()

def verificar_login(username, senha):
    """Verificar credenciais"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, is_admin FROM usuarios WHERE username = ?", (username,))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario and hash_senha(senha) == usuario[2]:
        return {
            "id": usuario[0],
            "username": usuario[1],
            "is_admin": bool(usuario[3]),
            "autenticado": True
        }
    return None

def listar_relatorios(usuario_id=None):
    """Listar relatórios"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.username as criador
        FROM relatorios r
        LEFT JOIN usuarios u ON r.criado_por = u.id
        ORDER BY r.criado_em DESC
    ''')
    
    relatorios = []
    for row in cursor.fetchall():
        relatorios.append({
            'id': row[0],
            'titulo': row[1],
            'link_powerbi': row[2],
            'descricao': row[3],
            'categoria': row[4],
            'criado_por': row[5],
            'criado_em': row[6],
            'criador': row[7]
        })
    
    conn.close()
    return relatorios

def criar_relatorio(titulo, link_powerbi, descricao, categoria, criado_por):
    """Criar novo relatório"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO relatorios (titulo, link_powerbi, descricao, categoria, criado_por)
            VALUES (?, ?, ?, ?, ?)
        ''', (titulo, link_powerbi, descricao, categoria, criado_por))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar relatório: {e}")
        return False
    finally:
        conn.close()

def excluir_relatorio(relatorio_id):
    """Excluir relatório"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM relatorios WHERE id = ?", (relatorio_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao excluir relatório: {e}")
        return False
    finally:
        conn.close()

def listar_usuarios():
    """Listar todos os usuários"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, is_admin, criado_em FROM usuarios ORDER BY criado_em DESC")
    
    usuarios = []
    for row in cursor.fetchall():
        usuarios.append({
            'id': row[0],
            'username': row[1],
            'is_admin': bool(row[2]),
            'criado_em': row[3]
        })
    
    conn.close()
    return usuarios

def criar_usuario(username, senha, is_admin=False):
    """Criar novo usuário"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    try:
        password_hash = hash_senha(senha)
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, is_admin)
            VALUES (?, ?, ?)
        ''', (username, password_hash, 1 if is_admin else 0))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuário já existe
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return False
    finally:
        conn.close()

def atualizar_senha(usuario_id, nova_senha):
    """Atualizar senha do usuário"""
    conn = sqlite3.connect("portal.db")
    cursor = conn.cursor()
    
    try:
        nova_hash = hash_senha(nova_senha)
        cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (nova_hash, usuario_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao atualizar senha: {e}")
        return False
    finally:
        conn.close()

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

# ========== INICIALIZAR ==========
init_db()

# ========== VERIFICAR LOGIN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    # PÁGINA DE LOGIN
    st.title("🔐 Portal Power BI - Grupo FRT")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", border=False):
            st.subheader("Acesso ao Sistema")
            
            username = st.text_input("**Usuário**", placeholder="Digite seu usuário")
            senha = st.text_input("**Senha**", type="password", placeholder="Digite sua senha")
            
            if st.form_submit_button("🚀 **Entrar no Portal**", use_container_width=True):
                if username and senha:
                    usuario = verificar_login(username, senha)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.success(f"Bem-vindo, {usuario['username']}!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        st.markdown("---")
        with st.expander("ℹ️ **Informações de acesso**"):
            st.write("**Primeiro acesso:**")
            st.code("Usuário: admin")
            st.code("Senha: admin123")
            st.write("**Importante:** Altere a senha após o primeiro acesso!")
    
    st.stop()

# ========== APÓS LOGIN ==========
usuario = st.session_state.usuario
is_admin = usuario['is_admin']

# ========== SIDEBAR (MENU) ==========
with st.sidebar:
    st.title(f"👤 {usuario['username']}")
    
    if is_admin:
        st.success("⚙️ **Administrador**")
    
    st.markdown("---")
    
    menu = st.radio(
        "**Menu Principal**",
        ["📊 Dashboard", "➕ Novo Relatório", "👥 Gerenciar Usuários", "⚙️ Minha Conta"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if st.button("🚪 **Sair do Sistema**", use_container_width=True, type="secondary"):
        st.session_state.usuario = None
        st.rerun()

# ========== DASHBOARD ==========
if menu == "📊 Dashboard":
    st.title("📊 Dashboard de Relatórios")
    
    # Buscar relatórios
    relatorios = listar_relatorios(usuario['id'])
    
    if not relatorios:
        st.info("📝 **Nenhum relatório cadastrado.**")
        st.info("Adicione seu primeiro relatório usando o menu '➕ Novo Relatório'")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            categorias = list(set([r['categoria'] for r in relatorios]))
            filtro_cat = st.selectbox("Filtrar por categoria", ["Todas"] + categorias)
        with col2:
            buscar = st.text_input("🔍 Buscar relatório", placeholder="Digite título ou descrição...")
        
        # Aplicar filtros
        relatorios_filtrados = relatorios
        if filtro_cat != "Todas":
            relatorios_filtrados = [r for r in relatorios_filtrados if r['categoria'] == filtro_cat]
        
        if buscar:
            buscar_lower = buscar.lower()
            relatorios_filtrados = [
                r for r in relatorios_filtrados 
                if buscar_lower in r['titulo'].lower() or 
                (r['descricao'] and buscar_lower in r['descricao'].lower())
            ]
        
        # Exibir relatórios
        st.subheader(f"📋 Relatórios Disponíveis ({len(relatorios_filtrados)})")
        
        for relatorio in relatorios_filtrados:
            # Usar uma chave de sessão para controlar visibilidade
            chave_visivel = f"visivel_{relatorio['id']}"
            
            # Inicializar se não existir
            if chave_visivel not in st.session_state:
                st.session_state[chave_visivel] = False
            
            with st.expander(f"📈 {relatorio['titulo']} - *{relatorio['categoria']}*"):
                
                # Informações do relatório
                col_info, col_btn = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Descrição:** {relatorio['descricao'] or 'Sem descrição'}")
                    st.write(f"**Criado por:** {relatorio['criador'] or 'Sistema'}")
                    st.write(f"**Data:** {relatorio['criado_em']}")
                
                with col_btn:
                    # Botão para abrir em nova aba
                    link = relatorio['link_powerbi']
                    if "embed" in link:
                        link = link.replace("embed", "view")
                    
                    # Botão PEQUENO para caber na caixa
                    st.markdown(f"""
                    <div style="margin-bottom: 5px;">
                        <a href="{link}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #2196F3;
                                color: white;
                                border-radius: 4px;
                                padding: 6px 8px;
                                font-size: 11px;
                                font-weight: 600;
                                text-align: center;
                                cursor: pointer;
                                transition: all 0.2s;
                                border: 1px solid #1976D2;
                                height: 30px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                gap: 4px;
                            "
                            onmouseover="this.style.backgroundColor='#1976D2'; this.style.transform='scale(1.02)';"
                            onmouseout="this.style.backgroundColor='#2196F3'; this.style.transform='scale(1)';"
                            >
                            <span>📊</span>
                            <span>Abrir</span>
                            </div>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão para mostrar/ocultar link
                    if st.button("🔗 Link", key=f"link_{relatorio['id']}", type="secondary", 
                                use_container_width=True):
                        st.session_state[chave_visivel] = not st.session_state[chave_visivel]
                        st.rerun()
                
                # Mostrar link se visível
                if st.session_state[chave_visivel]:
                    st.markdown("---")
                    st.write("**Link do Relatório:**")
                    st.code(link, language="text")
                    
                    # Botões compactos
                    col_copy, col_close = st.columns(2)
                    with col_copy:
                        if st.button("📋 Copiar", key=f"copy_{relatorio['id']}"):
                            st.success("✅ Link copiado!")
                    with col_close:
                        if st.button("❌ Fechar", key=f"hide_{relatorio['id']}"):
                            st.session_state[chave_visivel] = False
                            st.rerun()
                
                # Botões de admin
                if is_admin or relatorio['criado_por'] == usuario['id']:
                    st.markdown("---")
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Editar", key=f"edit_{relatorio['id']}"):
                            st.session_state['editar_relatorio'] = relatorio['id']
                    with col_del:
                        if st.button("🗑️ Excluir", key=f"del_{relatorio['id']}"):
                            if excluir_relatorio(relatorio['id']):
                                st.success("✅ Relatório excluído!")
                                st.rerun()

# ========== NOVO RELATÓRIO ==========
elif menu == "➕ Novo Relatório":
    st.title("➕ Adicionar Novo Relatório")
    
    with st.form("novo_relatorio_form", clear_on_submit=True):
        st.subheader("📝 Informações do Relatório")
        
        titulo = st.text_input("**Título do Relatório** *", 
                             placeholder="Ex: Dashboard de Vendas Trimestral")
        
        link = st.text_area("**Link do Power BI** *", 
                          height=120,
                          placeholder="""Cole aqui o link gerado pelo Power BI...

Exemplo: https://app.powerbi.com/view?r=eyJrIjoi...""")
        
        col1, col2 = st.columns(2)
        with col1:
            descricao = st.text_area("**Descrição**", 
                                   placeholder="Descreva o conteúdo deste relatório...",
                                   height=100)
        with col2:
            categoria = st.selectbox("**Categoria**", 
                                   ["Geral", "Vendas", "Marketing", "Financeiro", "RH", "Operações", "Logística"])
        
        st.markdown("---")
        
        if st.form_submit_button("💾 **Salvar Relatório**", type="primary", use_container_width=True):
            if not titulo or not link:
                st.error("❌ **Preencha os campos obrigatórios (*)!**")
            elif not validar_link_powerbi(link):
                st.error("❌ **Link inválido! Certifique-se que é um link do Power BI.**")
            else:
                if criar_relatorio(titulo, link, descricao, categoria, usuario['id']):
                    st.success("✅ **Relatório adicionado com sucesso!**")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ **Erro ao salvar relatório!**")

# ========== GERENCIAR USUÁRIOS ==========
elif menu == "👥 Gerenciar Usuários":
    if not is_admin:
        st.error("⛔ **Acesso restrito!** Apenas administradores podem gerenciar usuários.")
        st.stop()
    
    st.title("👥 Gerenciamento de Usuários")
    
    tab1, tab2 = st.tabs(["📋 **Lista de Usuários**", "👤 **Criar Novo Usuário**"])
    
    with tab1:
        usuarios_db = listar_usuarios()
        
        if not usuarios_db:
            st.info("📝 Nenhum usuário cadastrado.")
        else:
            for user in usuarios_db:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**👤 {user['username']}**")
                        st.write(f"Tipo: {'👑 Administrador' if user['is_admin'] else '👤 Usuário comum'}")
                        st.write(f"Criado em: {user['criado_em']}")
                    
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{user['id']}", type="secondary"):
                            st.session_state.editar_usuario = user['id']
                    
                    with col3:
                        if user['username'] != "admin":
                            if st.button("🗑️ Excluir", key=f"delete_{user['id']}", type="secondary"):
                                conn = sqlite3.connect("portal.db")
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM usuarios WHERE id = ?", (user['id'],))
                                conn.commit()
                                conn.close()
                                st.success(f"✅ Usuário {user['username']} excluído!")
                                st.rerun()
    
    with tab2:
        st.subheader("Criar Novo Usuário")
        
        with st.form("criar_usuario_form"):
            novo_username = st.text_input("Nome de usuário *", placeholder="Ex: joao.silva")
            nova_senha = st.text_input("Senha *", type="password", placeholder="Mínimo 6 caracteres")
            confirmar_senha = st.text_input("Confirmar senha *", type="password")
            is_admin = st.checkbox("É administrador?")
            
            if st.form_submit_button("👤 **Criar Usuário**", type="primary"):
                if not all([novo_username, nova_senha, confirmar_senha]):
                    st.error("❌ Preencha todos os campos!")
                elif nova_senha != confirmar_senha:
                    st.error("❌ As senhas não coincidem!")
                elif len(nova_senha) < 6:
                    st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                else:
                    if criar_usuario(novo_username, nova_senha, is_admin):
                        st.success(f"✅ Usuário **{novo_username}** criado com sucesso!")
                    else:
                        st.error("❌ Este nome de usuário já existe!")

# ========== MINHA CONTA ==========
elif menu == "⚙️ Minha Conta":
    st.title("⚙️ Minha Conta")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("👤 Perfil")
        st.write(f"**Usuário:** {usuario['username']}")
        st.write(f"**Tipo:** {'Administrador' if is_admin else 'Usuário'}")
    
    with col2:
        st.subheader("🔐 Alterar Senha")
        
        with st.form("alterar_senha_form"):
            senha_atual = st.text_input("Senha atual *", type="password")
            nova_senha = st.text_input("Nova senha *", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
            
            if st.form_submit_button("🔄 **Alterar Senha**", type="primary"):
                if not all([senha_atual, nova_senha, confirmar_senha]):
                    st.error("❌ Preencha todos os campos!")
                elif nova_senha != confirmar_senha:
                    st.error("❌ As novas senhas não coincidem!")
                elif len(nova_senha) < 6:
                    st.error("❌ A nova senha deve ter pelo menos 6 caracteres!")
                else:
                    usuario_verificado = verificar_login(usuario['username'], senha_atual)
                    if not usuario_verificado:
                        st.error("❌ Senha atual incorreta!")
                    else:
                        if atualizar_senha(usuario['id'], nova_senha):
                            st.success("✅ Senha alterada com sucesso!")
                            st.info("⚠️ Faça logout e login novamente para aplicar as alterações.")
                        else:
                            st.error("❌ Erro ao alterar senha!")

# ========== RODAPÉ ==========
st.markdown("---")
st.caption(f"📊 Portal Power BI v1.0 | 🏢 Grupo FRT | 👤 {usuario['username']} | 🌐 paineis-grupofrt.streamlit.app")