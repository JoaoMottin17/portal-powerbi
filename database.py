import sqlite3
import bcrypt
import json
from datetime import datetime

class Database:
    def __init__(self, db_path="portal.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Criar conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        return conn
    
    def init_database(self):
        """Inicializar tabelas do banco"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN DEFAULT 1
        )
        ''')
        
        # Tabela de relatórios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            link_powerbi TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT DEFAULT 'Geral',
            tags TEXT,  # JSON com tags
            criado_por INTEGER,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN DEFAULT 1,
            FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        )
        ''')
        
        # Tabela de logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_acesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            relatorio_id INTEGER,
            data_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (relatorio_id) REFERENCES relatorios(id)
        )
        ''')
        
        # Criar usuário admin inicial se não existir
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            senha_hash = self.hash_password("admin123")
            cursor.execute('''
            INSERT INTO usuarios (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@portal.com', senha_hash, 1))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash da senha com bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verificar senha"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # --- CRUD Usuários ---
    def criar_usuario(self, username, email, password, is_admin=False):
        """Criar novo usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            senha_hash = self.hash_password(password)
            cursor.execute('''
            INSERT INTO usuarios (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
            ''', (username, email, senha_hash, 1 if is_admin else 0))
            
            conn.commit()
            user_id = cursor.lastrowid
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError as e:
            return {"success": False, "error": "Usuário ou email já existe"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def autenticar_usuario(self, username, password):
        """Autenticar usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, username, email, password_hash, is_admin 
        FROM usuarios 
        WHERE username = ? AND ativo = 1
        ''', (username,))
        
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario and self.verify_password(password, usuario['password_hash']):
            return {
                "id": usuario['id'],
                "username": usuario['username'],
                "email": usuario['email'],
                "is_admin": bool(usuario['is_admin']),
                "autenticado": True
            }
        return None
    
    def listar_usuarios(self):
        """Listar todos os usuários"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, username, email, is_admin, criado_em, ativo 
        FROM usuarios 
        ORDER BY criado_em DESC
        ''')
        
        usuarios = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return usuarios
    
    def atualizar_usuario(self, user_id, **kwargs):
        """Atualizar dados do usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        campos_permitidos = ['username', 'email', 'is_admin', 'ativo']
        updates = []
        valores = []
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'password' and valor:
                    valor = self.hash_password(valor)
                    campo = 'password_hash'
                updates.append(f"{campo} = ?")
                valores.append(valor)
        
        if not updates:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        valores.append(user_id)
        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ?"
        
        try:
            cursor.execute(query, valores)
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def excluir_usuario(self, user_id):
        """Excluir usuário (soft delete)"""
        return self.atualizar_usuario(user_id, ativo=0)
    
    # --- CRUD Relatórios ---
    def criar_relatorio(self, titulo, link_powerbi, descricao="", categoria="Geral", tags=None, criado_por=None):
        """Adicionar novo relatório"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else "[]"
        
        try:
            cursor.execute('''
            INSERT INTO relatorios (titulo, link_powerbi, descricao, categoria, tags, criado_por)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (titulo, link_powerbi, descricao, categoria, tags_json, criado_por))
            
            conn.commit()
            rel_id = cursor.lastrowid
            return {"success": True, "relatorio_id": rel_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def listar_relatorios(self, ativos=True, usuario_id=None):
        """Listar relatórios"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
        SELECT r.*, u.username as criador
        FROM relatorios r
        LEFT JOIN usuarios u ON r.criado_por = u.id
        WHERE r.ativo = ?
        '''
        params = [1 if ativos else 0]
        
        if usuario_id:
            query += " AND (r.criado_por = ? OR ? = ?)"
            params.extend([usuario_id, usuario_id, usuario_id])
        
        query += " ORDER BY r.criado_em DESC"
        
        cursor.execute(query, params)
        relatorios = [dict(row) for row in cursor.fetchall()]
        
        # Converter tags JSON
        for rel in relatorios:
            if rel['tags']:
                rel['tags'] = json.loads(rel['tags'])
        
        conn.close()
        return relatorios
    
    def atualizar_relatorio(self, relatorio_id, **kwargs):
        """Atualizar relatório"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        campos_permitidos = ['titulo', 'link_powerbi', 'descricao', 'categoria', 'tags', 'ativo']
        updates = []
        valores = []
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'tags' and valor:
                    valor = json.dumps(valor)
                updates.append(f"{campo} = ?")
                valores.append(valor)
        
        if not updates:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        valores.append(relatorio_id)
        query = f"UPDATE relatorios SET {', '.join(updates)} WHERE id = ?"
        
        try:
            cursor.execute(query, valores)
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def excluir_relatorio(self, relatorio_id):
        """Excluir relatório (soft delete)"""
        return self.atualizar_relatorio(relatorio_id, ativo=0)
    
    def registrar_acesso(self, usuario_id, relatorio_id):
        """Registrar acesso ao relatório"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO logs_acesso (usuario_id, relatorio_id)
        VALUES (?, ?)
        ''', (usuario_id, relatorio_id))
        
        conn.commit()
        conn.close()