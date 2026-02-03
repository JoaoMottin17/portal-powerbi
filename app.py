import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ========== CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Portal Power BI - Grupo FRT",
    page_icon="📊",
    layout="wide"
)

# ========== CONSTANTES ==========
CATEGORIAS_PADRAO = [
    "Geral", 
    "Vendas", 
    "Marketing", 
    "Financeiro", 
    "RH", 
    "Operações", 
    "Logística",
    "Suprimentos",
    "Operacional"
]

# ========== BANCO DE DADOS ==========
def init_db():
    """Inicializar banco de dados - APENAS SE NÃO EXISTIR"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Criar tabela de usuários se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0,
        categorias_permitidas TEXT DEFAULT '[]',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Criar tabela de relatórios se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relatorios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        link_powerbi TEXT NOT NULL,
        descricao TEXT,
        categoria TEXT DEFAULT 'Geral',
        criado_por INTEGER,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (criado_por) REFERENCES usuarios(id)
    )''')
    
    # VERIFICAR E ADICIONAR COLUNAS FALTANTES
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    
    # Adicionar coluna categorias_permitidas se não existir
    if 'categorias_permitidas' not in colunas_existentes:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN categorias_permitidas TEXT DEFAULT '[]'")
    
    # Adicionar coluna atualizado_em em relatorios se não existir
    cursor.execute("PRAGMA table_info(relatorios)")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    
    if 'atualizado_em' not in colunas_existentes:
        cursor.execute("ALTER TABLE relatorios ADD COLUMN atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    # Verificar se existe admin
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    admin_existe = cursor.fetchone()[0]
    
    if admin_existe == 0:
        # Criar admin padrão
        password_hash = hashlib.sha256(b"admin123_salt_grupofrt").hexdigest()
        todas_categorias = str(CATEGORIAS_PADRAO)
        
        cursor.execute('''
        INSERT INTO usuarios (username, password_hash, is_admin, categorias_permitidas)
        VALUES (?, ?, ?, ?)''', ('admin', password_hash, 1, todas_categorias))
    
    # ATUALIZAR USUÁRIOS EXISTENTES PARA TEREM CATEGORIAS
    cursor.execute("UPDATE usuarios SET categorias_permitidas = ? WHERE categorias_permitidas IS NULL OR categorias_permitidas = ''", 
                   (str(CATEGORIAS_PADRAO),))
    
    conn.commit()
    conn.close()

# ========== FUNÇÕES AUXILIARES ==========
def hash_senha(senha):
    """Hash para senhas"""
    return hashlib.sha256(f"{senha}_salt_grupofrt".encode()).hexdigest()

def verificar_login(username, senha):
    """Verificar credenciais"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, is_admin, categorias_permitidas FROM usuarios WHERE username = ?", (username,))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario and hash_senha(senha) == usuario[2]:
        # Converter string de categorias para lista
        import ast
        categorias = []
        if usuario[4]:
            try:
                categorias = ast.literal_eval(usuario[4])
            except:
                categorias = CATEGORIAS_PADRAO
        else:
            categorias = CATEGORIAS_PADRAO
        
        return {
            "id": usuario[0],
            "username": usuario[1],
            "is_admin": bool(usuario[3]),
            "categorias_permitidas": categorias,
            "autenticado": True
        }
    return None

def listar_relatorios(usuario):
    """Listar relatórios que o usuário tem permissão para ver"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    if usuario['is_admin'] or not usuario['categorias_permitidas']:
        cursor.execute('''
            SELECT r.*, u.username as criador
            FROM relatorios r
            LEFT JOIN usuarios u ON r.criado_por = u.id
            ORDER BY r.criado_em DESC
        ''')
    else:
        categorias_placeholders = ','.join(['?'] * len(usuario['categorias_permitidas']))
        query = f'''
            SELECT r.*, u.username as criador
            FROM relatorios r
            LEFT JOIN usuarios u ON r.criado_por = u.id
            WHERE r.categoria IN ({categorias_placeholders})
            ORDER BY r.criado_em DESC
        '''
        cursor.execute(query, usuario['categorias_permitidas'])
    
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
            'atualizado_em': row[7] if len(row) > 7 else row[6],
            'criador': row[8] if len(row) > 8 else 'Sistema'
        })
    
    conn.close()
    return relatorios

def obter_relatorio_por_id(relatorio_id):
    """Obter um relatório específico pelo ID"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.username as criador
        FROM relatorios r
        LEFT JOIN usuarios u ON r.criado_por = u.id
        WHERE r.id = ?
    ''', (relatorio_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'titulo': row[1],
            'link_powerbi': row[2],
            'descricao': row[3],
            'categoria': row[4],
            'criado_por': row[5],
            'criado_em': row[6],
            'atualizado_em': row[7] if len(row) > 7 else row[6],
            'criador': row[8] if len(row) > 8 else 'Sistema'
        }
    return None

def criar_relatorio(titulo, link_powerbi, descricao, categoria, criado_por):
    """Criar novo relatório"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO relatorios (titulo, link_powerbi, descricao, categoria, criado_por)
            VALUES (?, ?, ?, ?, ?)
        ''', (titulo, link_powerbi, descricao, categoria, criado_por))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao criar relatório: {e}")
        return False
    finally:
        conn.close()

def atualizar_relatorio(relatorio_id, titulo, link_powerbi, descricao, categoria):
    """Atualizar relatório existente"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE relatorios 
            SET titulo = ?, link_powerbi = ?, descricao = ?, categoria = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (titulo, link_powerbi, descricao, categoria, relatorio_id))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar relatório: {e}")
        return False
    finally:
        conn.close()

def excluir_relatorio(relatorio_id):
    """Excluir relatório"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM relatorios WHERE id = ?", (relatorio_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir relatório: {e}")
        return False
    finally:
        conn.close()

def listar_usuarios():
    """Listar todos os usuários"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, is_admin, categorias_permitidas, criado_em FROM usuarios ORDER BY criado_em DESC")
    
    usuarios = []
    for row in cursor.fetchall():
        import ast
        categorias = []
        if row[3]:
            try:
                categorias = ast.literal_eval(row[3])
            except:
                categorias = []
        else:
            categorias = CATEGORIAS_PADRAO
        
        usuarios.append({
            'id': row[0],
            'username': row[1],
            'is_admin': bool(row[2]),
            'categorias_permitidas': categorias,
            'criado_em': row[4]
        })
    
    conn.close()
    return usuarios

def obter_usuario_por_id(usuario_id):
    """Obter usuário por ID"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, is_admin, categorias_permitidas FROM usuarios WHERE id = ?", (usuario_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        import ast
        categorias = []
        if row[3]:
            try:
                categorias = ast.literal_eval(row[3])
            except:
                categorias = []
        else:
            categorias = CATEGORIAS_PADRAO
        
        return {
            'id': row[0],
            'username': row[1],
            'is_admin': bool(row[2]),
            'categorias_permitidas': categorias
        }
    return None

def criar_usuario(username, senha, is_admin=False, categorias_permitidas=None):
    """Criar novo usuário"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        if categorias_permitidas is None:
            if is_admin:
                categorias_permitidas = CATEGORIAS_PADRAO
            else:
                categorias_permitidas = ["Geral"]
        
        password_hash = hash_senha(senha)
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, is_admin, categorias_permitidas)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, 1 if is_admin else 0, str(categorias_permitidas)))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("❌ Este nome de usuário já existe!")
        return False
    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")
        return False
    finally:
        conn.close()

def atualizar_usuario(usuario_id, username=None, is_admin=None, categorias_permitidas=None):
    """Atualizar informações do usuário"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if username:
            updates.append("username = ?")
            params.append(username)
        
        if is_admin is not None:
            updates.append("is_admin = ?")
            params.append(1 if is_admin else 0)
        
        if categorias_permitidas is not None:
            updates.append("categorias_permitidas = ?")
            params.append(str(categorias_permitidas))
        
        if updates:
            query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ?"
            params.append(usuario_id)
            cursor.execute(query, params)
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("❌ Este nome de usuário já existe!")
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False
    finally:
        conn.close()

def atualizar_senha(usuario_id, nova_senha):
    """Atualizar senha do usuário"""
    conn = sqlite3.connect("portal.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        nova_hash = hash_senha(nova_senha)
        cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (nova_hash, usuario_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar senha: {e}")
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

# ========== INICIALIZAR BANCO ==========
init_db()

# ========== VERIFICAR LOGIN ==========
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    # PÁGINA DE LOGIN
    # ========== LOGO NO LOGIN ==========
    col_logo, col_titulo = st.columns([1, 3])
    with col_logo:
        # Para usar uma imagem local, você pode:
        # 1. Salvar a imagem na mesma pasta como "logo.png"
        # 2. Usar uma URL de imagem online
        # 3. Usar um ícone do Streamlit
        
        # Opção 1: Imagem local (descomente e ajuste o caminho)
        st.image("logo.png", width=550)
        
        # Opção 2: URL de imagem online
        # st.image("https://via.placeholder.com/150x150/0E2C4D/FFFFFF?text=FRT", width=150)
        
        # Opção 3: Ícone grande do Streamlit
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="font-size: 60px; color: #0E2C4D;"></h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col_titulo:
        st.title("🔐 Portal Power BI")
        st.subheader("Grupo FRT")
    
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
                        st.success(f"✅ Bem-vindo, {usuario['username']}!")
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
    # ========== LOGO NO SIDEBAR ==========
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #0E2C4D;"> Grupo FRT</h2>
        <p style="color: #666; font-size: 14px;">Portal Power BI</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.write(f"👤 **Usuário:** {usuario['username']}")
    
    if is_admin:
        st.success("⚙️ **Administrador**")
    else:
        cats = usuario['categorias_permitidas']
        if len(cats) > 3:
            st.info(f"📊 **Categorias:** {', '.join(cats[:3])}...")
        else:
            st.info(f"📊 **Categorias:** {', '.join(cats)}")
    
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

# ========== HEADER COM LOGO EM TODAS AS PÁGINAS ==========
# Esta parte aparece em todas as páginas após login

col_logo_header, col_titulo_header = st.columns([1, 4])
with col_logo_header:
    # Aqui você pode colocar uma imagem menor para o header
    st.markdown("""
    <div style="text-align: left;">
        <h3 style="color: #0E2C4D; margin: 0;"> FRT </h3>
    </div>
    """, unsafe_allow_html=True)

with col_titulo_header:
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Relatórios")
    elif menu == "➕ Novo Relatório":
        if 'editar_relatorio' in st.session_state:
            st.title("✏️ Editar Relatório")
        else:
            st.title("➕ Adicionar Novo Relatório")
    elif menu == "👥 Gerenciar Usuários":
        st.title("👥 Gerenciamento de Usuários")
    elif menu == "⚙️ Minha Conta":
        st.title("⚙️ Minha Conta")

st.markdown("---")

# ========== CONTEÚDO DAS PÁGINAS ==========
if menu == "📊 Dashboard":
    # Buscar relatórios
    relatorios = listar_relatorios(usuario)
    
    if not relatorios:
        st.info("📝 **Nenhum relatório disponível nas suas categorias.**")
        if not is_admin and usuario['categorias_permitidas']:
            st.info(f"Suas categorias: {', '.join(usuario['categorias_permitidas'])}")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            categorias_disponiveis = list(set([r['categoria'] for r in relatorios]))
            filtro_cat = st.selectbox("Filtrar por categoria", ["Todas"] + sorted(categorias_disponiveis))
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
            with st.expander(f"📈 {relatorio['titulo']} - *{relatorio['categoria']}*"):
                col_info, col_btn = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Descrição:** {relatorio['descricao'] or 'Sem descrição'}")
                    st.write(f"**Criado por:** {relatorio['criador'] or 'Sistema'}")
                    st.write(f"**Criado em:** {relatorio['criado_em']}")
                    if 'atualizado_em' in relatorio and relatorio['atualizado_em'] != relatorio['criado_em']:
                        st.write(f"**Atualizado em:** {relatorio['atualizado_em']}")
                
                with col_btn:
                    link = relatorio['link_powerbi']
                    if "embed" in link:
                        link = link.replace("embed", "view")
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 10px;">
                        <a href="{link}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #2196F3;
                                color: white;
                                border-radius: 4px;
                                padding: 8px 12px;
                                font-size: 12px;
                                font-weight: 600;
                                text-align: center;
                                cursor: pointer;
                                border: 1px solid #1976D2;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                gap: 4px;
                            ">
                            <span>📊</span>
                            <span>Abrir Power BI</span>
                            </div>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.write("**Link do Relatório:**")
                st.code(link, language="text")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📋 Copiar Link", key=f"copy_{relatorio['id']}"):
                        st.success("✅ Link copiado!")
                
                if is_admin or relatorio['criado_por'] == usuario['id']:
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{relatorio['id']}"):
                            st.session_state['editar_relatorio'] = relatorio['id']
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Excluir", key=f"del_{relatorio['id']}"):
                            if excluir_relatorio(relatorio['id']):
                                st.success("✅ Relatório excluído!")
                                st.rerun()

elif menu == "➕ Novo Relatório":
    if 'editar_relatorio' in st.session_state:
        relatorio = obter_relatorio_por_id(st.session_state['editar_relatorio'])
        modo_edicao = True if relatorio else False
    else:
        modo_edicao = False
    
    with st.form("novo_relatorio_form", clear_on_submit=not modo_edicao):
        if modo_edicao:
            titulo = st.text_input("**Título do Relatório** *", value=relatorio['titulo'])
            link = st.text_area("**Link do Power BI** *", value=relatorio['link_powerbi'], height=120)
            descricao = st.text_area("**Descrição**", value=relatorio['descricao'] or "", height=100)
            categoria = st.selectbox("**Categoria**", CATEGORIAS_PADRAO,
                                   index=CATEGORIAS_PADRAO.index(relatorio['categoria']) if relatorio['categoria'] in CATEGORIAS_PADRAO else 0)
        else:
            titulo = st.text_input("**Título do Relatório** *", placeholder="Ex: Dashboard de Vendas Trimestral")
            link = st.text_area("**Link do Power BI** *", height=120,
                              placeholder="Cole aqui o link gerado pelo Power BI...")
            descricao = st.text_area("**Descrição**", placeholder="Descreva o conteúdo deste relatório...", height=100)
            categoria = st.selectbox("**Categoria**", CATEGORIAS_PADRAO)
        
        st.markdown("---")
        
        if modo_edicao:
            col_salvar, col_cancelar = st.columns(2)
            with col_salvar:
                if st.form_submit_button("💾 **Salvar Alterações**", type="primary", use_container_width=True):
                    if not titulo or not link:
                        st.error("❌ **Preencha os campos obrigatórios (*)!**")
                    elif not validar_link_powerbi(link):
                        st.error("❌ **Link inválido! Certifique-se que é um link do Power BI.**")
                    else:
                        if atualizar_relatorio(relatorio['id'], titulo, link, descricao, categoria):
                            st.success("✅ **Relatório atualizado com sucesso!**")
                            del st.session_state['editar_relatorio']
                            st.rerun()
            
            with col_cancelar:
                if st.form_submit_button("❌ **Cancelar**", type="secondary", use_container_width=True):
                    del st.session_state['editar_relatorio']
                    st.rerun()
        else:
            if st.form_submit_button("💾 **Salvar Relatório**", type="primary", use_container_width=True):
                if not titulo or not link:
                    st.error("❌ **Preencha os campos obrigatórios (*)!**")
                elif not validar_link_powerbi(link):
                    st.error("❌ **Link inválido! Certifique-se que é um link do Power BI.**")
                else:
                    if criar_relatorio(titulo, link, descricao, categoria, usuario['id']):
                        st.success("✅ **Relatório adicionado com sucesso!**")
                        st.rerun()

elif menu == "👥 Gerenciar Usuários":
    if not is_admin:
        st.error("⛔ **Acesso restrito!** Apenas administradores podem gerenciar usuários.")
        st.stop()
    
    if 'editar_usuario_id' in st.session_state:
        tab1, tab2 = st.tabs(["✏️ **Editar Usuário**", "📋 **Lista de Usuários**"])
    else:
        tab1, tab2 = st.tabs(["👤 **Criar Novo Usuário**", "📋 **Lista de Usuários**"])
    
    with tab1:
        if 'editar_usuario_id' in st.session_state:
            user_data = obter_usuario_por_id(st.session_state['editar_usuario_id'])
            modo_edicao = True
        else:
            user_data = None
            modo_edicao = False
        
        with st.form("criar_editar_usuario_form"):
            if modo_edicao:
                novo_username = st.text_input("Nome de usuário *", value=user_data['username'])
                alterar_senha = st.checkbox("Alterar senha?")
                if alterar_senha:
                    nova_senha = st.text_input("Nova senha *", type="password", placeholder="Mínimo 6 caracteres")
                    confirmar_senha = st.text_input("Confirmar nova senha *", type="password")
                else:
                    nova_senha = ""
                    confirmar_senha = ""
            else:
                novo_username = st.text_input("Nome de usuário *", placeholder="Ex: joao.silva")
                nova_senha = st.text_input("Senha *", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_senha = st.text_input("Confirmar senha *", type="password")
            
            is_admin = st.checkbox("É administrador?", value=user_data['is_admin'] if modo_edicao else False)
            
            categorias_selecionadas = []
            if not is_admin:
                st.markdown("### 📊 Categorias Permitidas")
                st.write("Selecione as categorias que este usuário poderá visualizar:")
                
                if modo_edicao and user_data:
                    categorias_selecionadas = user_data['categorias_permitidas']
                
                num_colunas = 3
                colunas = st.columns(num_colunas)
                
                for i, categoria in enumerate(CATEGORIAS_PADRAO):
                    col_idx = i % num_colunas
                    with colunas[col_idx]:
                        checked = categoria in categorias_selecionadas
                        if st.checkbox(categoria, value=checked, key=f"cat_{categoria}"):
                            if categoria not in categorias_selecionadas:
                                categorias_selecionadas.append(categoria)
                
                if not categorias_selecionadas:
                    categorias_selecionadas = ["Geral"]
            
            col_salvar, col_cancelar = st.columns(2)
            
            with col_salvar:
                if modo_edicao:
                    btn_text = "💾 **Salvar Alterações**"
                else:
                    btn_text = "👤 **Criar Usuário**"
                
                if st.form_submit_button(btn_text, type="primary", use_container_width=True):
                    if modo_edicao:
                        if alterar_senha and nova_senha and confirmar_senha:
                            if nova_senha != confirmar_senha:
                                st.error("❌ As senhas não coincidem!")
                            elif len(nova_senha) < 6:
                                st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                            else:
                                if atualizar_senha(user_data['id'], nova_senha):
                                    st.success("✅ Senha atualizada!")
                        
                        success = atualizar_usuario(
                            user_data['id'],
                            username=novo_username,
                            is_admin=is_admin,
                            categorias_permitidas=categorias_selecionadas if not is_admin else CATEGORIAS_PADRAO
                        )
                        
                        if success:
                            st.success("✅ Usuário atualizado com sucesso!")
                            if 'editar_usuario_id' in st.session_state:
                                del st.session_state['editar_usuario_id']
                            st.rerun()
                    
                    else:
                        if not all([novo_username, nova_senha, confirmar_senha]):
                            st.error("❌ Preencha todos os campos!")
                        elif nova_senha != confirmar_senha:
                            st.error("❌ As senhas não coincidem!")
                        elif len(nova_senha) < 6:
                            st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                        else:
                            if criar_usuario(novo_username, nova_senha, is_admin, 
                                           categorias_selecionadas if not is_admin else None):
                                st.success(f"✅ Usuário **{novo_username}** criado com sucesso!")
                                st.rerun()
            
            with col_cancelar:
                if modo_edicao and st.form_submit_button("❌ **Cancelar**", type="secondary", use_container_width=True):
                    if 'editar_usuario_id' in st.session_state:
                        del st.session_state['editar_usuario_id']
                    st.rerun()
    
    with tab2:
        usuarios_db = listar_usuarios()
        
        if not usuarios_db:
            st.info("📝 Nenhum usuário cadastrado.")
        else:
            for user in usuarios_db:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**👤 {user['username']}**")
                        st.write(f"**Tipo:** {'👑 Administrador' if user['is_admin'] else '👤 Usuário comum'}")
                        if not user['is_admin']:
                            st.write(f"**Categorias permitidas:** {', '.join(user['categorias_permitidas'][:5])}")
                            if len(user['categorias_permitidas']) > 5:
                                st.write(f"... e mais {len(user['categorias_permitidas']) - 5}")
                        st.write(f"**Criado em:** {user['criado_em']}")
                    
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{user['id']}", type="secondary"):
                            st.session_state['editar_usuario_id'] = user['id']
                            st.rerun()
                    
                    with col3:
                        if user['username'] != "admin":
                            if st.button("🗑️ Excluir", key=f"delete_{user['id']}", type="secondary"):
                                conn = sqlite3.connect("portal.db", check_same_thread=False)
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM usuarios WHERE id = ?", (user['id'],))
                                conn.commit()
                                conn.close()
                                st.success(f"✅ Usuário {user['username']} excluído!")
                                st.rerun()

elif menu == "⚙️ Minha Conta":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("👤 Perfil")
        st.write(f"**Usuário:** {usuario['username']}")
        st.write(f"**Tipo:** {'Administrador' if is_admin else 'Usuário'}")
        if not is_admin:
            st.write(f"**Categorias permitidas:**")
            for cat in usuario['categorias_permitidas']:
                st.write(f"• {cat}")
    
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

# ========== RODAPÉ ==========
st.markdown("---")
st.caption(f"📊 Portal Power BI v1.0 |  Grupo FRT | 👤 {usuario['username']}")

# ========== INSTRUÇÕES PARA USAR UMA IMAGEM REAL ==========
# Descomente e ajuste o código abaixo para usar uma imagem real:

# 1. Coloque sua imagem na pasta do projeto com o nome "logo.png"
# 2. Descomente as linhas abaixo onde estão os comentários sobre imagem

# No login (por volta da linha 330):
   # st.image("logo.png", width=150)

# No sidebar (por volta da linha 380):
   # st.image("logo.png", width=100)

# No header (por volta da linha 410):
   # st.image("logo.png", width=50)