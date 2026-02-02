import streamlit as st
from database import Database

class AuthSystem:
    def __init__(self):
        self.db = Database()
    
    def login_page(self):
        """Página de login"""
        st.title("🔐 Login - Portal Power BI")
        
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Preencha todos os campos!")
                else:
                    usuario = self.db.autenticar_usuario(username, password)
                    if usuario:
                        st.session_state["usuario"] = usuario
                        st.success(f"Bem-vindo, {usuario['username']}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")
        
        # Credenciais padrão
        with st.expander("Credenciais padrão"):
            st.write("**Admin:** admin / admin123")
            st.write("**Importante:** Altere a senha após o primeiro acesso!")
    
    def is_logged_in(self):
        """Verificar se usuário está logado"""
        return "usuario" in st.session_state and st.session_state["usuario"]["autenticado"]
    
    def get_current_user(self):
        """Obter usuário atual"""
        return st.session_state.get("usuario")
    
    def is_admin(self):
        """Verificar se usuário é admin"""
        usuario = self.get_current_user()
        return usuario and usuario.get("is_admin", False)
    
    def logout(self):
        """Fazer logout"""
        if "usuario" in st.session_state:
            del st.session_state["usuario"]
        st.rerun()
    
    def proteger_pagina(self):
        """Proteger página - redirecionar para login se não estiver autenticado"""
        if not self.is_logged_in():
            self.login_page()
            st.stop()