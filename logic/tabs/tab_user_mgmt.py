import streamlit as st
import pandas as pd
from logic.auth_manager import load_users, add_user, delete_user, save_users, update_user
from logic.data_manager import santralleri_yukle, santral_kaydet, santral_sil
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_user_mgmt_tab(is_super_admin=False):
    st.header("👥 Kullanıcı ve Yetki Yönetimi")
    st.info("Sistemdeki kullanıcıların rollerini, erişim yetkilerini ve santral tanımlamalarını buradan yönetebilirsiniz.")
    
    users = load_users()
    plants = santralleri_yukle()

    # 1. Bekleyen Onaylar (Pending Users)
    pending = {u: d for u, d in users.items() if d.get("status") == "pending"}
    if pending:
        st.subheader("⏳ Onay Bekleyen Başvurular")
        for u, d in pending.items():
            with st.expander(f"👤 Başvuru: {u} ({d.get('full_name', '-')})", expanded=True):
                col_p1, col_p2, col_p3 = st.columns([1, 1, 1])
                with col_p1:
                    app_role = st.selectbox("Atanacak Rol", ["User", "Admin", "SuperAdmin"], key=f"role_app_{u}")
                with col_p2:
                    app_plants = st.multiselect("Yetkili Santraller", options=list(plants.keys()), default=["merkez"], key=f"plant_app_{u}")
                
                with col_p3:
                    st.write("") # Spacer
                    btn_app = st.button(f"✅ Onayla ve Yetkilendir", key=f"btn_app_{u}", use_container_width=True)
                    btn_rej = st.button(f"❌ Başvuruyu Sil", key=f"btn_rej_{u}", use_container_width=True)
                    
                    if btn_app:
                        update_user(u, status="active", role=app_role, assigned_plants=app_plants)
                        st.success(f"{u} başarıyla '{app_role}' olarak onaylandı.")
                        st.rerun()
                    if btn_rej:
                        delete_user(u)
                        st.warning(f"{u} başvurusu silindi.")
                        st.rerun()
        st.divider()

    # 2. Kullanıcı Listesi ve Detaylı Tablo
    st.subheader("📊 Mevcut Kullanıcılar")
    user_list_data = []
    for u, d in users.items():
        if d.get("status") == "active":
            user_list_data.append({
                "Kullanıcı": u,
                "Tam Ad": d.get("full_name", "-"),
                "Rol": d.get("role", "User"),
                "Santraller": ", ".join(d.get("assigned_plants", ["merkez"])),
                "Durum": d.get("status", "active")
            })
    
    if user_list_data:
        df_users = pd.DataFrame(user_list_data)
        st.dataframe(df_users, use_container_width=True, hide_index=True)

    # 3. Kullanıcı Yetki ve Bilgi Düzenleme
    with st.expander("🛠️ Kullanıcı Yetkilerini Düzenle"):
        active_users = [u for u, d in users.items() if d.get("status") == "active"]
        selected_u = st.selectbox("Düzenlenecek Kullanıcı", active_users)
        
        if selected_u:
            u_info = users[selected_u]
            with st.form(f"edit_user_{selected_u}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Tam Ad", value=u_info.get("full_name", ""))
                    new_role = st.selectbox("Rol", ["User", "Admin", "SuperAdmin"], 
                                            index=["User", "Admin", "SuperAdmin"].index(u_info.get("role", "User")))
                with col2:
                    current_assigned = u_info.get("assigned_plants", ["merkez"])
                    new_plants = st.multiselect("Erişim Yetkili Santraller", 
                                                options=list(plants.keys()),
                                                default=[p for p in current_assigned if p in plants])
                
                c_btn1, c_btn2 = st.columns([1, 1])
                save_u = c_btn1.form_submit_button("💾 Bilgileri Güncelle", use_container_width=True)
                delete_u = c_btn2.form_submit_button("🗑️ Kullanıcıyı Sil", use_container_width=True)
                
                if save_u:
                    update_user(selected_u, role=new_role, full_name=new_name, assigned_plants=new_plants)
                    st.success(f"{selected_u} güncellendi.")
                    st.rerun()
                
                if delete_u:
                    if selected_u == st.session_state.get('username'):
                        st.error("Kendi hesabınızı silemezsiniz!")
                    else:
                        success, msg = delete_user(selected_u)
                        if success:
                            st.warning(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # 4. Santral (Plant) Yönetimi
    if is_super_admin:
        st.divider()
        st.subheader("🏢 Santral (Tesis) Yönetimi")
        
        # Mevcut Santraller Tablosu
        plant_list = []
        for pid, pinfo in plants.items():
            plant_list.append({"ID": pid, "İsim": pinfo.get("name", pid), "Konum": pinfo.get("location", "-")})
        st.table(pd.DataFrame(plant_list))
        
        with st.expander("➕ Yeni Santral Ekle / 🗑️ Sil"):
            tab_add, tab_del = st.tabs(["🚀 Yeni Ekle", "❌ Santral Sil"])
            
            with tab_add:
                with st.form("add_plant_form"):
                    p1, p2, p3 = st.columns(3)
                    new_pid = p1.text_input("Santral ID (Küçük harf, boşluksuz)", placeholder="örn: akdeniz_01")
                    new_pname = p2.text_input("Santral Tam Adı", placeholder="Akdeniz Bölge Santrali")
                    new_ploc = p3.text_input("Konum (Şehir/İlçe)", placeholder="Antalya")
                    
                    if st.form_submit_button("🏢 Santrali Kaydet"):
                        if new_pid and new_pname:
                            santral_kaydet(new_pid.lower().strip(), {"name": new_pname, "location": new_ploc})
                            st.success(f"'{new_pname}' sisteme eklendi.")
                            st.rerun()
                        else:
                            st.error("Lütfen ID ve İsim alanlarını doldurun.")
            
            with tab_del:
                del_pid = st.selectbox("Silinecek Santral", [p for p in plants.keys() if p != "merkez"])
                if st.button("🗑️ Santrali Sistemden Kaldır", type="primary"):
                    success, msg = santral_sil(del_pid)
                    if success:
                        st.warning(msg)
                        st.rerun()
                    else:
                        st.error(msg)
