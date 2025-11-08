import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# --- Option Lists ---
TYPE_OPTIONS = ["Lost", "Found"]
CATEGORY_OPTIONS = ["Pets", "Electronics", "Bags", "Jewelry", "Personal Items", "Others"]
CITY_OPTIONS = ["Kuwait City", "Salmiya", "Hawally", "Jahra", "Farwaniya", "Ahmadi", "Mubarak Al-Kabeer"]

# --- File Config ---
DATA_FILE = "announcements.csv"
IMAGES_FOLDER = "announcement_images"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# --- Data Handling ---
def load_data():
    columns = ["ID", "Type", "Category", "City", "Description",
               "Image1", "Image2", "Image3", "Phone", "Date",
               "EventDate", "DeletePassword", "Resolved"]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        for c in columns:
            if c not in df.columns:
                df[c] = ""
        df["Resolved"] = df["Resolved"].fillna("False").astype(str).str.lower().map({
            "true": True, "false": False, "1": True, "0": False
        }).fillna(False).astype(bool)
        return df[columns]
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def save_images(files):
    paths = []
    for file in files[:3]:
        if file is not None:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}_{file.name}"
            filepath = os.path.join(IMAGES_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(file.getbuffer())
            paths.append(filepath)
    while len(paths) < 3:
        paths.append("")
    return paths

def try_rerun():
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()
    except Exception:
        st.info("Please refresh manually to see changes.")

# --- Load Data ---
df = load_data()

# --- Sidebar Navigation ---
page = st.sidebar.radio("Navigate", ["🏠 Home", "📢 View Announcements"])

# ------------------- 🏠 HOME PAGE -------------------
if page == "🏠 Home":
    st.title("🧭 Lost & Found in Kuwait")
    st.write("Find what you’ve lost or help others recover what they’ve misplaced.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Search for an Item", use_container_width=True):
            st.session_state.page = "📢 View Announcements"
            st.session_state.filter_type = "All"
            st.session_state.show_form = False
            try_rerun()
    with col2:
        if st.button("📦 Report an Item", use_container_width=True):
            st.session_state.show_form = True

    st.markdown("---")

    # --- Post Form ---
    if st.session_state.get("show_form", False):
        st.header("Post a Lost or Found Item")
        f1, f2, f3 = st.columns(3)
        with f1:
            post_type = st.radio("Type", TYPE_OPTIONS, horizontal=True)
        with f2:
            category = st.selectbox("Category", CATEGORY_OPTIONS)
        with f3:
            city = st.selectbox("City / Area", CITY_OPTIONS)

        description = st.text_area("Description of the item")
        event_date = st.date_input(f"Date the item was {post_type.lower()}")
        phone = st.text_input("Contact Phone Number (8 digits)")
        delete_password = st.text_input("Set a delete password for this post", type="password")
        uploaded_files = st.file_uploader("Upload up to 3 pictures",
                                          type=["png", "jpg", "jpeg"], accept_multiple_files=True)

        if st.button("Submit Announcement"):
            if not description:
                st.error("Please enter a description.")
            elif len(phone) != 8 or not phone.isdigit():
                st.error("Phone number must be exactly 8 digits.")
            elif not delete_password:
                st.error("Please set a delete password.")
            else:
                image_paths = save_images(uploaded_files)
                new_id = str(len(df) + 1)
                new_post = {
                    "ID": new_id,
                    "Type": post_type.lower(),
                    "Category": category,
                    "City": city,
                    "Description": description,
                    "Image1": image_paths[0],
                    "Image2": image_paths[1],
                    "Image3": image_paths[2],
                    "Phone": phone,
                    "Date": datetime.today().strftime("%Y-%m-%d"),
                    "EventDate": event_date.strftime("%Y-%m-%d"),
                    "DeletePassword": delete_password.strip(),
                    "Resolved": False,
                }
                df.loc[len(df)] = new_post
                save_data(df)
                st.success("Announcement posted successfully!")
                st.session_state.show_form = False
                try_rerun()

    st.markdown("### 🆕 Recently Posted Items")
    recent = df.sort_values("Date", ascending=False).head(6)
    if recent.empty:
        st.info("No posts yet — be the first to add one!")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(recent.iterrows()):
            with cols[i % 3]:
                # --- Images Horizontally ---
                images = [row["Image1"], row["Image2"], row["Image3"]]
                images = [img for img in images if img and os.path.exists(img)]
                if images:
                    img_cols = st.columns(len(images))
                    for j, img_path in enumerate(images):
                        with img_cols[j]:
                            st.image(img_path, use_container_width=True)

                st.markdown(f"**{row['Category']}** {'🔴' if row['Type']=='lost' else '🟢'}")
                st.caption(f"{row['City']} • {row['EventDate']}")
                if (datetime.today() - pd.to_datetime(row["Date"])).days <= 3:
                    st.markdown("🔥 New!")
                with st.expander("Details / Contact Owner"):
                    st.write(row["Description"])
                    st.write(f"📞 {row['Phone']}")
                    if row["Resolved"]:
                        st.success("✅ Resolved")
                    else:
                        st.warning("🔴 Not resolved")

# ------------------- 📢 VIEW ANNOUNCEMENTS -------------------
elif page == "📢 View Announcements":
    st.title("📢 Lost & Found Announcements")

    search_query = st.text_input("🔍 Search by keyword (e.g., 'wallet', 'dog', 'bag')")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        current_type = st.session_state.get("filter_type", "All")
        if current_type in TYPE_OPTIONS:
            default_index = TYPE_OPTIONS.index(current_type) + 1
        else:
            default_index = 0
        filter_type = st.selectbox("Type", ["All"] + TYPE_OPTIONS, index=default_index)
    with col2:
        filter_city = st.selectbox("City", ["All"] + CITY_OPTIONS)
    with col3:
        filter_category = st.selectbox("Category", ["All"] + CATEGORY_OPTIONS)
    with col4:
        start_date = st.date_input("Start Date", value=None)
    with col5:
        end_date = st.date_input("End Date", value=None)
    with col6:
        show_resolved = st.checkbox("Include resolved", value=False)

    filtered = df.copy()
    if filter_type != "All":
        filtered = filtered[filtered["Type"] == filter_type.lower()]
    if filter_city != "All":
        filtered = filtered[filtered["City"] == filter_city]
    if filter_category != "All":
        filtered = filtered[filtered["Category"] == filter_category]
    if not show_resolved:
        filtered = filtered[filtered["Resolved"] == False]
    if search_query:
        filtered = filtered[filtered["Description"].str.contains(search_query, case=False, na=False)]
    if start_date:
        filtered = filtered[pd.to_datetime(filtered["EventDate"]) >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[pd.to_datetime(filtered["EventDate"]) <= pd.to_datetime(end_date)]

    if filtered.empty:
        st.info("No results found.")
    else:
        st.markdown("### Results")
        cols = st.columns(3)
        for i, (_, row) in enumerate(filtered.sort_values("Date", ascending=False).iterrows()):
            with cols[i % 3]:
                # --- Images Horizontally ---
                images = [row["Image1"], row["Image2"], row["Image3"]]
                images = [img for img in images if img and os.path.exists(img)]
                if images:
                    img_cols = st.columns(len(images))
                    for j, img_path in enumerate(images):
                        with img_cols[j]:
                            st.image(img_path, use_container_width=True)

                st.markdown(f"**{row['Category']}** ({'🔴 Lost' if row['Type']=='lost' else '🟢 Found'})")
                st.caption(f"{row['City']} • {row['EventDate']}")
                if (datetime.today() - pd.to_datetime(row["Date"])).days <= 3:
                    st.markdown("🔥 New!")
                with st.expander("Details / Contact Owner"):
                    st.write(row["Description"])
                    st.write(f"📞 {row['Phone']}")

                    # --- Resolved Toggle ---
                    if row["Resolved"]:
                        st.success("✅ Resolved")
                        if st.button(f"Mark as Unresolved ({row['ID']})"):
                            df.loc[df["ID"] == row["ID"], "Resolved"] = False
                            save_data(df)
                            st.info("Post marked as unresolved.")
                            try_rerun()
                    else:
                        st.warning("🔴 Not resolved")
                        if st.button(f"Mark as Resolved ({row['ID']})"):
                            df.loc[df["ID"] == row["ID"], "Resolved"] = True
                            save_data(df)
                            st.success("Post marked as resolved.")
                            try_rerun()

                    # --- Delete ---
                    delete_pw = st.text_input(f"Delete password for ID {row['ID']}", type="password", key=f"delete_{row['ID']}")
                    if st.button(f"Delete Post ({row['ID']})"):
                        if delete_pw == row["DeletePassword"]:
                            df = df[df["ID"] != row["ID"]]
                            save_data(df)
                            st.success("Post deleted successfully.")
                            try_rerun()
                        else:
                            st.error("Incorrect delete password.")
