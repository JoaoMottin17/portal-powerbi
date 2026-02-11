import streamlit as st

from database import Database


class AuthSystem:
    def __init__(self):
        self.db = Database()

    def login_page(self):
        st.title("Login - Portal Power BI")

        with st.form("login_form"):
            username = st.text_input("Usuario")
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
                        st.error("Usuario ou senha incorretos!")

        with st.expander("Informacoes de acesso"):
            st.write("Use as credenciais definidas pelo administrador.")

    def is_logged_in(self):
        return "usuario" in st.session_state and st.session_state["usuario"]["autenticado"]

    def get_current_user(self):
        return st.session_state.get("usuario")

    def is_admin(self):
        usuario = self.get_current_user()
        return usuario and usuario.get("is_admin", False)

    def logout(self):
        if "usuario" in st.session_state:
            del st.session_state["usuario"]
        st.rerun()

    def proteger_pagina(self):
        if not self.is_logged_in():
            self.login_page()
            st.stop()
