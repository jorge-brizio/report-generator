import streamlit as st
import pandas as pd

st.set_page_config(page_title="Zammad Ticket Report Generator", layout="wide")

st.title("Report Generator")
st.write("Upload **all your Zammad Excel exports** at once (`.xlsx`) to instantly generate the comprehensive combined report (test groups automatically excluded).")

uploaded_files = st.file_uploader(
    "Choose Zammad Excel files", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    created_dfs = []
    closed_dfs = []
    
    for file in uploaded_files:
        try:
            df = pd.read_excel(file, header=2)
            fname = file.name.lower()
            if 'closed' in fname:
                closed_dfs.append(df)
            else:
                created_dfs.append(df)
        except Exception as e:
            st.warning(f"Could not read {file.name}: {e}")
            
    if created_dfs:
        df = pd.concat(created_dfs, ignore_index=True)
        
        # 1. Drop export metadata footer rows where State or Ticket ID is missing
        if 'State' in df.columns:
            df = df.dropna(subset=['State'])
        if '#' in df.columns:
            df = df.dropna(subset=['#'])
            df = df.drop_duplicates(subset=['#'])
            
        # 2. Permanent exclusions: test group, Partner Search, and Users groups
        excluded_groups = ['test group', 'Partner Search', 'Users']
        if 'Group' in df.columns:
            df = df[~df['Group'].isin(excluded_groups)]
            
        # 3. Categorize request types (keeping general support)
        def categorize_title(title):
            t = str(title).lower()
            if 'partnering offer draft' in t or 'new partner offer' in t:
                return 'New partnering offer drafts'
            elif 'partner search' in t or 'partner contact via offer' in t:
                return 'Partner search'
            else:
                return 'Other / General Support'
                
        if 'Title' in df.columns:
            df['Request_Type_Derived'] = df['Title'].apply(categorize_title)
            
        total_tickets = len(df)
        st.success(f"Successfully loaded {total_tickets} active tickets (Test Group, Partner Search, Users, and export metadata excluded).")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ticket State")
            state_counts = df['State'].value_counts()
            state_df = pd.DataFrame({
                'Count': state_counts,
                '% of Total': (state_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(state_df, use_container_width=True)
            
            st.subheader("Channel")
            channel_counts = df['Create Channel'].value_counts(dropna=False)
            channel_df = pd.DataFrame({
                'Count': channel_counts,
                '% of Total': (channel_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(channel_df, use_container_width=True)

        with col2:
            st.subheader("Agent / Workload (Group)")
            group_counts = df['Group'].value_counts(dropna=False)
            group_df = pd.DataFrame({
                'Count': group_counts,
                '% of Total': (group_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(group_df, use_container_width=True)
            
            st.subheader("Type of Request")
            req_counts = df['Request_Type_Derived'].value_counts(dropna=False)
            req_df = pd.DataFrame({
                'Count': req_counts,
                '% of Total': (req_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(req_df, use_container_width=True)
            
    else:
        st.error("Please upload valid Zammad ticket export files.")
else:
    st.info("👈 Upload your Zammad `.xlsx` files above to get started.")