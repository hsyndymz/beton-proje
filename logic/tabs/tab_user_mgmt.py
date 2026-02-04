import streamlit as st
import pandas as pd
from logic.auth_manager import load_users, add_user, delete_user, save_users, update_user
from logic.data_manager import santralleri_yukle, santral_kaydet, santral_sil
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_user_mgmt_tab(is_super_admin=False):
    st.subheader("👥 Kullanıcı ve Yetki Yönetimi")
    users = load_users()
    plants = santralleri_yukle()

    # Bekleyen Onaylar
    pending = {u: d for u, d in users.items() if d.get("status") == "pending"}
    for u, d in pending.items():
        if st.button(f"✅ Onayla: {u}"):
            users[u]["status"] = "active"
            save_users(users)
            st.rerun()

    # Santral Yönetimi
    if is_super_admin:
        with st.expander("🏢 Santral Yönetimi"):
            new_pid = st.text_input("Santral ID")
            new_pname = st.text_input("Santral Adı")
            if st.button("🚀 Kaydet"):
                santral_kaydet(new_pid, {"name": new_pname})
                st.rerun()

    # Kullanıcı Listesi
    st.table(pd.DataFrame([{"U": k, "R": v['role']} for k, v in users.items()]))
