import streamlit as st
import pandas as pd
from logic.data_manager import santralleri_yukle, santral_kaydet, santral_sil
from logic.auth_manager import load_users, add_user, delete_user, save_users, update_user

def render_tab_management(is_super_admin=False):
    st.subheader("👥 Kullanıcı ve Yetki Yönetimi")
    
    users = load_users()
    
    # 0. Bekleyen Onaylar
    pending_users = {u: d for u, d in users.items() if d.get("status") == "pending"}
    if pending_users:
        st.markdown("### ⏳ Bekleyen Üyelik Onayları")
        for p_uname, p_data in pending_users.items():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                c1.write(f"**{p_data.get('full_name')}** (@{p_uname})")
                c2.info("Onay bekliyor...")
                if c3.button("✅ Onayla", key=f"app_{p_uname}"):
                    users[p_uname]["status"] = "active"
                    save_users(users)
                    st.success(f"{p_uname} onaylandı.")
                    st.rerun()
                if c4.button("❌ Reddet", key=f"rej_{p_uname}"):
                    del users[p_uname]
                    save_users(users)
                    st.warning(f"{p_uname} başvurusu reddedildi.")
                    st.rerun()
        st.markdown("---")
    
    users = load_users() # Reload in case of changes
    
    # 1. Kullanıcı Listesi
    st.markdown("### Mevcut Kullanıcılar")
    df_users = []
    for uname, data in users.items():
        df_users.append({
            "Kullanıcı Adı": uname, 
            "Ad Soyad": data.get('full_name', '-'), 
            "Yetki": data.get('role', 'User'),
            "Durum": data.get('status', 'active')
        })
    st.table(pd.DataFrame(df_users))
    
    # 1.5. Santral Yönetimi (Sadece SuperAdmin)
    plants = santralleri_yukle()
    if is_super_admin:
        st.markdown("---")
        st.markdown("### 🏭 Santral Yönetimi")
        
        with st.expander("🏢 Santral Yönetim Paneli", expanded=True):
            df_plants = [{"ID": pid, "Ad": pd.get("name") if isinstance(pd, dict) else str(pd), 
                          "Konum": pd.get("location", "-") if isinstance(pd, dict) else "-", 
                          "Yönetici": pd.get("manager", "-") if isinstance(pd, dict) else "-"} 
                         for pid, pd in plants.items()]
            st.table(pd.DataFrame(df_plants))
            
            st.markdown("#### ➕ Yeni Santral Ekle")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                new_pid = st.text_input("Santral ID (Örn: ankara_1)", key="new_pid")
                new_pname = st.text_input("Santral Adı", key="new_pname")
            with c_p2:
                new_ploc = st.text_input("Konum/Şehir", key="new_ploc")
                new_pman = st.text_input("Santral Yöneticisi", key="new_pman")
                if st.button("🚀 Santrali Kaydet", use_container_width=True):
                    if new_pid and new_pname:
                        santral_kaydet(new_pid, {"name": new_pname, "location": new_ploc, "manager": new_pman})
                        st.success(f"Santral '{new_pname}' eklendi.")
                        st.rerun()
                    else: st.error("ID ve Ad zorunludur.")
            
            st.markdown("---")
            st.markdown("#### 📝 Santral Düzenle / Sil")
            edit_p_list = list(plants.keys())
            edit_pid = st.selectbox("Düzenlenecek Santral", edit_p_list, key="edit_pid_sel")
            if edit_pid:
                p_data = plants[edit_pid]
                ce_p1, ce_p2 = st.columns(2)
                with ce_p1:
                    edit_pname = st.text_input("Yeni Santral Adı", value=p_data["name"], key="edit_pname")
                    edit_pman = st.text_input("Yeni Yönetici", value=p_data.get("manager", ""), key="edit_pman")
                with ce_p2:
                    edit_ploc = st.text_input("Yeni Konum", value=p_data.get("location", ""), key="edit_ploc")
                
                ce_btns1, ce_btns2 = st.columns(2)
                with ce_btns1:
                    if st.button("💾 Değişiklikleri Kaydet", key="btn_save_plant"):
                        santral_kaydet(edit_pid, {"name": edit_pname, "location": edit_ploc, "manager": edit_pman})
                        st.success("Santral bilgileri güncellendi.")
                        st.rerun()
                with ce_btns2:
                    if st.button("🗑️ Santrali Sil", key="btn_del_plant", type="primary"):
                        success, msg = santral_sil(edit_pid)
                        if success:
                            st.warning(msg)
                            st.rerun()
                        else: st.error(msg)
    else:
        st.info("💡 Santral tanımlama yetkisi sadece SuperAdmin'e aittir.")
    
    # 2. Yeni Kullanıcı Ekle
    with st.expander("➕ Yeni Kullanıcı Tanımla"):
        c_u1, c_u2 = st.columns(2)
        with c_u1:
            new_u = st.text_input("Kullanıcı Adı", key="new_u_name")
            new_p = st.text_input("Şifre", type="password", key="new_u_pass")
        with c_u2:
            new_f = st.text_input("Ad Soyad", key="new_u_full")
            new_r = st.selectbox("Yetki Seviyesi", ["User", "Admin", "SuperAdmin"], key="new_u_role")
            
        new_up = st.multiselect("Yetkili Olacağı Santraller", options=list(plants.keys()), 
                                 default=["merkez"], format_func=lambda x: plants[x]["name"],
                                 key="new_u_plants")

        if st.button("✅ Kullanıcıyı Kaydet", use_container_width=True):
            if new_u and new_p:
                success, msg = add_user(new_u, new_p, new_r, new_f, assigned_plants=new_up)
                if success: 
                    st.success(msg)
                    st.rerun()
                else: st.error(msg)
            else: st.error("Kullanıcı adı ve şifre boş bırakılamaz!")
            
    # 2.5. Kullanıcı Bilgilerini Düzenle
    if is_super_admin:
        with st.expander("📝 Kullanıcı Bilgilerini Düzenle"):
            def sync_user_edit_fields():
                selected_u = st.session_state.get("edit_u_sel")
                if selected_u and selected_u in users:
                    u_data = users[selected_u]
                    st.session_state["edit_u_f"] = u_data.get('full_name', '')
                    st.session_state["edit_u_r"] = u_data.get('role', 'User')
                    st.session_state["edit_u_s"] = u_data.get('status', 'active')
                    st.session_state["edit_u_p"] = u_data.get('assigned_plants', ["merkez"])

            edit_u = st.selectbox("Düzenlenecek Kullanıcı", list(users.keys()), key="edit_u_sel", on_change=sync_user_edit_fields)
            if edit_u and "edit_u_f" not in st.session_state: sync_user_edit_fields()

            if edit_u:
                u_data = users[edit_u]
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_f = st.text_input("Yeni Ad Soyad", value=u_data.get('full_name', ''), key="edit_u_f")
                    edit_r = st.selectbox("Yeni Yetki", ["User", "Admin", "SuperAdmin"], 
                                          index=["User", "Admin", "SuperAdmin"].index(u_data.get('role', 'User')), key="edit_u_r")
                with col_e2:
                    edit_s = st.selectbox("Yeni Durum", ["active", "pending", "suspended"],
                                          index=["active", "pending", "suspended"].index(u_data.get('status', 'active')), key="edit_u_s")
                
                edit_p = st.multiselect("Yetkili Olacağı Santraller", options=list(plants.keys()), 
                                        default=u_data.get('assigned_plants', ['merkez']),
                                        format_func=lambda x: plants.get(x, {}).get("name", x), key="edit_u_p")

                if st.button("💾 Kullanıcıyı Güncelle"):
                    update_user(edit_u, full_name=edit_f, role=edit_r, status=edit_s, assigned_plants=edit_p)
                    st.success(f"{edit_u} güncellendi.")
                    st.rerun()
