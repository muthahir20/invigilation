import streamlit as st
from db import admin_login, process_excel, get_filtered_duties, engine, get_dashboard_stats, get_fn_an_count, update_admin_password, transfer_duty_session, swap_duties_session, delete_duty_session, add_new_duty,transfer_multiple_duties, get_duties, delete_multiple_duties,add_multiple_duties, get_session_report, generate_staff_pdf, generate_session_pdf, get_staff_report, update_staff_credentials
from ui import apply_ui
import pandas as pd
from sqlalchemy import text


apply_ui()

# SESSION
if "admin" not in st.session_state:
    st.session_state.admin = None

st.markdown('<div class="title">🛠️ Admin Panel</div>', unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if not st.session_state.admin:

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        admin = admin_login(username.strip(), password.strip())

        if admin:
            st.session_state.admin = {
                "id": admin[0],
                "role": admin[1]
            }
            st.rerun()
        else:
            st.error("Invalid credentials")

# ---------------- AFTER LOGIN ----------------
else:
    admin = st.session_state.admin

    st.success(f"Logged in as {admin['role']}")

    if st.button("Logout"):
        st.session_state.admin = None
        st.rerun()

    # =========================================================
    # 📊 DASHBOARD (ALWAYS ON TOP)
    # =========================================================
    st.markdown("## 📊 Admin Dashboard")

    staff_count, duty_count, session_count = get_dashboard_stats()
    fn_count, an_count = get_fn_an_count()

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f'<div class="stat-card fn">👨‍🏫 Staff<br>{staff_count}</div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="stat-card an">📝 Duties<br>{duty_count}</div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="stat-card other">📅 Sessions<br>{session_count}</div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="stat-card fn">FN: {fn_count}<br>AN: {an_count}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================
    # 📑 TABS BELOW DASHBOARD
    # =========================================================
    tab1, tab2, tab3, tab4, tab5, tab6= st.tabs([
        "🔍 View Duties",
        "📤 Upload Data",
        "🔐 Change Password",
        "⚙️ Manage Duties",
        "📄 Reports",
        "👤 Staff Credentials"
    ])

    # =========================================================
    # 📤 UPLOAD TAB
    # =========================================================
    with tab2:
        st.markdown("### 📤 Upload Staff & Duty Data")

        # ---------------- FILE UPLOAD ----------------
        file = st.file_uploader("Upload Excel File", type=["xlsx"])

        if file is not None:

            st.success(f"📄 Selected: {file.name}")

            # ---------------- MODE SELECTION ----------------
            upload_mode = st.radio(
                "Select Upload Mode",
                ["Append Data", "Overwrite Existing Data"],
                horizontal=True
            )

            # ---------------- WARNING FOR OVERWRITE ----------------
            confirm_overwrite = False

            if upload_mode == "Overwrite Existing Data":
                confirm_overwrite = st.checkbox(
                    "⚠️ I understand this will delete ALL existing data"
                )

            # ---------------- UPLOAD BUTTON ----------------
            if st.button("🚀 Upload Data"):

                try:
                    # Determine mode
                    mode = "append" if upload_mode == "Append Data" else "replace"

                    # Safety check
                    if mode == "replace" and not confirm_overwrite:
                        st.warning("⚠️ Please confirm overwrite before proceeding")
                        st.stop()

                    # Process file
                    process_excel(file.getvalue(), mode=mode)

                    # Success messages
                    if mode == "replace":
                        st.success("✅ Data overwritten successfully")
                    else:
                        st.success("✅ Data appended successfully")

                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

    # =========================================================
    # 🔍 FILTER TAB
    # =========================================================
    with tab1:
        st.markdown("## 🔍 View Duty Schedule")

        with engine.connect() as conn:
            session_df = pd.read_sql("SELECT DISTINCT session_text FROM duty ORDER BY session_text", conn)
            staff_df = pd.read_sql("SELECT staff_id, name, dept FROM staff ORDER BY staff_id", conn)

        sessions = ["All"] + session_df["session_text"].tolist()
        departments = ["All"] + sorted(staff_df["dept"].unique().tolist())
        staff_options = ["All"] + staff_df.apply(
            lambda x: f"{x['staff_id']} - {x['name']}", axis=1
        ).tolist()

        col1, col2, col3 = st.columns(3)

        with col1:
            selected_session = st.selectbox("Session", sessions)

        with col2:
            selected_dept = st.selectbox("Department", departments)

        with col3:
            selected_staff = st.multiselect("Staff", staff_options, default=["All"])

        if "All" in selected_staff:
            selected_ids = ["All"]
        else:
            selected_ids = [s.split(" - ")[0] for s in selected_staff]

        df = get_filtered_duties(selected_session, selected_dept, selected_ids)

        if not df.empty:

            st.download_button(
                "📥 Download Excel",
                df.to_csv(index=False),
                file_name="filtered_duties.csv",
                mime="text/csv"
            )

            st.markdown("### 📋 Duty List")

            grouped = df.groupby("session_text")

            for session, group in grouped:

                st.markdown(f"#### 📅 {session}")

                for _, row in group.iterrows():

                    if "FN" in session.upper():
                        card_class = "fn"
                    elif "AN" in session.upper():
                        card_class = "an"
                    else:
                        card_class = "other"

                    st.markdown(f"""
                    <div class="duty-card {card_class}">
                        <b>{row['staff_id']} - {row['name']}</b><br>
                        {row['dept']}
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.info("No duties found")

    # =========================================================
    # 🔐 PASSWORD TAB
    # =========================================================
    with tab3:
        st.markdown("## 🔐 Change Password")

        old_pass = st.text_input("Old Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")

        if st.button("Update Password"):

            if not old_pass or not new_pass:
                st.warning("Please fill all fields")

            elif new_pass != confirm_pass:
                st.error("Passwords do not match")

            elif len(new_pass) < 5:
                st.warning("Password must be at least 5 characters")

            else:
                success = update_admin_password(
                    admin["id"],
                    old_pass.strip(),
                    new_pass.strip()
                )

                if success:
                    st.success("✅ Password updated successfully")
                else:
                    st.error("❌ Old password is incorrect")
        with tab4:
            st.markdown("## ⚙️ Manage Duties")
            st.info("⚙️ Manage duties efficiently using transfer, swap, delete or add options")

            # Load data
            with engine.connect() as conn:
                staff_df = pd.read_sql("SELECT staff_id, name, dept FROM staff ORDER BY staff_id", conn)
                session_df = pd.read_sql("SELECT DISTINCT session_text FROM duty ORDER BY session_text", conn)

            staff_options = staff_df.apply(
                lambda x: f"{x['staff_id']} - {x['name']}", axis=1
            ).tolist()

            sessions = session_df["session_text"].tolist()

            # ================= SUB TABS =================
            sub1, sub2, sub3, sub4 = st.tabs([
                "🔄 Transfer",
                "🔁 Swap",
                "❌ Delete",
                "➕ Add"
            ])

            # =========================================================
            # 🔄 TRANSFER
            # =========================================================
            with sub1:
                st.markdown("### 🔄 Transfer Duties")

                # ---------------- STAFF SELECT ----------------
                col1, col2 = st.columns(2)

                with col1:
                    from_staff = st.selectbox("From Staff", staff_options, key="from_staff")

                with col2:
                    to_staff = st.selectbox("To Staff", staff_options, key="to_staff")

                from_id = from_staff.split(" - ")[0] if from_staff else None
                to_id = to_staff.split(" - ")[0] if to_staff else None

                # ---------------- LOAD DUTIES ----------------
                if from_id and to_id:

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 📌 From Staff Duties")

                        from_df = get_duties(from_id)
                        selected_sessions = []

                        if not from_df.empty:
                            for i, row in from_df.iterrows():
                                session = row["session_text"]

                                checked = st.checkbox(
                                    f"{session}",
                                    key=f"from_{i}"
                                )

                                if checked:
                                    selected_sessions.append(session)
                        else:
                            st.info("No duties assigned")

                    with col2:
                        st.markdown("#### 📥 To Staff Duties")

                        to_df = get_duties(to_id)

                        if not to_df.empty:
                            for _, row in to_df.iterrows():
                                st.markdown(f"""
                               
                                    <b>{row['session_text']}
                                
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No duties assigned")

                    # ---------------- ACTION ----------------
                    st.markdown("---")

                    if st.button("🚀 Transfer Selected Duties"):

                        if not selected_sessions:
                            st.warning("⚠️ Select at least one duty")
                        elif from_id == to_id:
                            st.warning("⚠️ Cannot transfer to same staff")
                        else:
                            transfer_multiple_duties(selected_sessions, from_id, to_id)
                            st.success("✅ Duties transferred successfully")
                            st.rerun()

            # =========================================================
            # 🔁 SWAP
            # =========================================================
            with sub2:
                st.markdown("### 🔁 Swap Duties")

                col1, col2 = st.columns(2)

                with col1:
                    staff1 = st.selectbox("Staff 1", staff_options, key="swap_1")

                with col2:
                    staff2 = st.selectbox("Staff 2", staff_options, key="swap_2")

                id1 = staff1.split(" - ")[0]
                id2 = staff2.split(" - ")[0]

                if id1 and id2:

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Staff 1 Duties")
                        df1 = get_duties(id1)

                        selected_1 = []
                        for i, row in df1.iterrows():
                            if st.checkbox(f"{row['session_text']}", key=f"s1_{i}"):
                                selected_1.append(row["session_text"])

                    with col2:
                        st.markdown("#### Staff 2 Duties")
                        df2 = get_duties(id2)

                        selected_2 = []
                        for i, row in df2.iterrows():
                            if st.checkbox(f"{row['session_text']}", key=f"s2_{i}"):
                                selected_2.append(row["session_text"])

                    if st.button("🔁 Swap Selected Duties"):

                        if not selected_1 or not selected_2:
                            st.warning("Select duties from both staff")

                        elif len(selected_1) != len(selected_2):
                            st.warning("Select equal number of duties")

                        else:
                            for s1, s2 in zip(selected_1, selected_2):
                                transfer_multiple_duties([s1], id1, id2)
                                transfer_multiple_duties([s2], id2, id1)

                            st.success("✅ Duties swapped")
                            st.rerun()

           
            # =========================================================
            # ❌ DELETE (UPDATED)
            # =========================================================
            with sub3:
                st.markdown("### ❌ Delete Duties")

                # ---------------- STAFF SELECT ----------------
                del_staff = st.selectbox("Select Staff", staff_options, key="del_staff")

                if del_staff:

                    staff_id = del_staff.split(" - ")[0]

                    st.markdown("#### 📋 Assigned Duties")

                    df = get_duties(staff_id)

                    selected_sessions = []

                    if not df.empty:

                        for i, row in df.iterrows():

                            session = row["session_text"]

                            checked = st.checkbox(
                                f"{session}",
                                key=f"del_{i}"
                            )

                            if checked:
                                selected_sessions.append(session)

                    else:
                        st.info("No duties assigned")

                    # ---------------- ACTION ----------------
                    st.markdown("---")

                    if st.button("🗑️ Delete Selected Duties"):

                        if not selected_sessions:
                            st.warning("⚠️ Please select at least one duty")

                        else:
                            delete_multiple_duties(staff_id, selected_sessions)
                            st.success("✅ Selected duties deleted successfully")
                            st.rerun()

           
            # =========================================================
            # ➕ ADD (UPDATED)
            # =========================================================
            with sub4:
                st.markdown("### ➕ Add Duties")

                # ---------------- STAFF SELECT ----------------
                selected_staff = st.selectbox("Select Staff", staff_options, key="add_staff")

                if selected_staff:

                    staff_id = selected_staff.split(" - ")[0]

                    # ---------------- EXISTING DUTIES ----------------
                    st.markdown("#### 📋 Current Duties")

                    df = get_duties(staff_id)
                    
                    existing_sessions = df["session_text"].tolist() if not df.empty else []

                    # Filter sessions
                    available_sessions = [s for s in sessions if s not in existing_sessions]

                    # new_sessions = st.multiselect(
                    #     "Select Sessions",
                    #     available_sessions,
                    #     help="Only unassigned sessions are shown"
                    # )

                    if not df.empty:
                        for _, row in df.iterrows():
                            st.markdown(f"""
                            <div class="duty-card">
                                <b> {row['session_text']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No duties assigned")

                    st.markdown("---")

                    # ---------------- SESSION SELECT ----------------
                    st.markdown("#### ➕ Add New Sessions")

                    col1, col2 = st.columns([2, 1])

                    with col1:

                        new_sessions = st.multiselect(
                        "Select Sessions",
                        available_sessions,
                        help="Only unassigned sessions are shown"
                    )

                    with col2:
                        add_btn = st.button("➕ Add Duties")

                    # ---------------- ACTION ----------------
                    if add_btn:

                        if not new_sessions:
                            st.warning("⚠️ Select at least one session")

                        else:
                            success = add_multiple_duties(staff_id, new_sessions)

                            if success:
                                st.success("✅ Duties added successfully")
                                st.rerun()
                            else:
                                st.warning("⚠️ No new duties added (duplicates skipped)")
        with tab5:
            st.markdown("## 📄 Reports")

            report1, report2 = st.tabs([
                "📅 Session Report",
                "👨‍🏫 Staff Report"
            ])

            with report1:
                st.markdown("### 📅 Session Report")

                session = st.selectbox("Select Session", sessions, key="report_session")

                if st.button("Generate Session Report"):

                    df = get_session_report(session)

                    if df.empty:
                        st.warning("No data found")
                    else:
                        file = generate_session_pdf(session, df)

                        with open(file, "rb") as f:
                            st.download_button(
                                "📥 Download PDF",
                                f,
                                file_name=file
                            )
            
            with report2:
                st.markdown("### 👨‍🏫 Staff Report")

                selected_staff = st.selectbox("Select Staff", staff_options, key="staff_report")

                if selected_staff:

                    staff_id = selected_staff.split(" - ")[0]
                    staff_name = selected_staff.split(" - ")[1]

                    dept = staff_df[staff_df["staff_id"] == staff_id]["dept"].values[0]

                    if st.button("Generate Staff Report"):

                        df = get_staff_report(staff_id)

                        if df.empty:
                            st.warning("No duties found")
                        else:
                            file = generate_staff_pdf(staff_name, dept, df)

                            with open(file, "rb") as f:
                                st.download_button(
                                    "📥 Download PDF",
                                    f,
                                    file_name=file
                                )
            with tab6:

                st.markdown("## 👤 Manage Staff Credentials")

                # Load staff
                with engine.connect() as conn:
                    staff_df = pd.read_sql("SELECT staff_id, name, email FROM staff ORDER BY staff_id", conn)

                staff_options = staff_df.apply(
                    lambda x: f"{x['staff_id']} - {x['name']}", axis=1
                ).tolist()

                selected_staff = st.selectbox("Select Staff", staff_options)

                if selected_staff:

                    staff_id = selected_staff.split(" - ")[0]

                    # Get current details
                    current = staff_df[staff_df["staff_id"] == staff_id].iloc[0]

                    st.markdown("### ✏️ Update Details")

                    col1, col2 = st.columns(2)

                    with col1:
                        new_email = st.text_input(
                            "Email",
                            value=current["email"] if current["email"] else ""
                        )

                    with col2:
                        new_password = st.text_input(
                            "New Password (Last 5 digits)",
                            type="password"
                        )

                    if st.button("Update Credentials"):

                        if not new_email:
                            st.warning("Email cannot be empty")

                        elif not new_password:
                            st.warning("Enter new password")

                        else:
                            update_staff_credentials(
                                staff_id,
                                new_email,
                                new_password
                            )

                            st.success("✅ Credentials updated successfully")
                            st.rerun()
