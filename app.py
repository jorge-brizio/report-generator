import streamlit as st
import pandas as pd

st.set_page_config(page_title="Report Generator", layout="wide")

st.title("Report Generator")
st.write("Upload **all your Zammad Excel exports** at once (`.xlsx`) to instantly generate the comprehensive combined report (test groups automatically excluded).")

# Enable multi-file upload
uploaded_files = st.file_uploader(
    "Choose Zammad Excel files", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    created_dfs = []
    closed_dfs = []
    
    # Categorize and read each uploaded file based on its filename
    for file in uploaded_files:
        try:
            df = pd.read_excel(file, header=2)
            filename_lower = file.name.lower()
            
            if 'created' in filename_lower:
                created_dfs.append(df)
            elif 'closed' in filename_lower:
                closed_dfs.append(df)
        except Exception as e:
            st.warning(f"Could not parse {file.name}: {e}")
            
    # Combine all created ticket datasets if any were uploaded
    if created_dfs:
        combined_created = pd.concat(created_dfs, ignore_index=True)
        
        # Remove duplicates if same tickets were exported across views
        if '#' in combined_created.columns:
            combined_created = combined_created.drop_duplicates(subset=['#'])
            
        # Filter out 'test group'
        if 'Group' in combined_created.columns:
            combined_created = combined_created[combined_created['Group'] != 'test group']
            
        total_tickets = len(combined_created)
        st.success(f"Successfully processed {len(uploaded_files)} file(s). Total unique active tickets combined: **{total_tickets}** (Test Group excluded).")
        
        # Display breakdown columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ticket State")
            state_counts = combined_created['State'].value_counts(dropna=False)
            state_df = pd.DataFrame({
                'Count': state_counts,
                '% of Total': (state_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(state_df, use_container_width=True)
            
            st.subheader("Channel")
            channel_counts = combined_created['Create Channel'].value_counts(dropna=False)
            channel_df = pd.DataFrame({
                'Count': channel_counts,
                '% of Total': (channel_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(channel_df, use_container_width=True)

        with col2:
            st.subheader("Agent / Workload (Group)")
            group_counts = combined_created['Group'].value_counts(dropna=False)
            group_df = pd.DataFrame({
                'Count': group_counts,
                '% of Total': (group_counts / total_tickets * 100).round(1).astype(str) + '%'
            })
            st.dataframe(group_df, use_container_width=True)

            # Derived Request Types
            st.subheader("Type of Request (Derived)")
            def categorize_title(title):
                t = str(title).lower()
                if 'partnering offer draft' in t or 'new partner offer' in t:
                    return 'New partnering offer drafts'
                elif 'partner search' in t or 'partner contact via offer' in t:
                    return 'Partner search'
                else:
                    return 'Other / General Support'
            
            if 'Title' in combined_created.columns:
                req_counts = combined_created['Title'].apply(categorize_title).value_counts()
                req_df = pd.DataFrame({
                    'Count': req_counts,
                    '% of Total': (req_counts / total_tickets * 100).round(1).astype(str) + '%'
                })
                st.dataframe(req_df, use_container_width=True)

        # Resolution Time Calculation if closed files were provided
        st.markdown("---")
        st.subheader("Other Metrics")
        if closed_dfs:
            combined_closed = pd.concat(closed_dfs, ignore_index=True)
            if 'Created At' in combined_closed.columns and 'Closed At' in combined_closed.columns:
                combined_closed['Created At'] = pd.to_datetime(combined_closed['Created At'], errors='coerce')
                combined_closed['Closed At'] = pd.to_datetime(combined_closed['Closed At'], errors='coerce')
                combined_closed['Resolution Time'] = combined_closed['Closed At'] - combined_closed['Created At']
                mean_res = combined_closed['Resolution Time'].mean()
                days = mean_res.days
                hours = mean_res.seconds // 3600
                st.metric(label="Mean Time to Resolution (Across Closed Datasets)", value=f"{days}d {hours}h")
        else:
            st.info("Tip: Upload your Closed ticket exports alongside Created exports to automatically compute resolution times.")
            
    else:
        st.error("No valid 'Created' ticket exports found in your selection. Please check your filenames.")
else:
    st.info("👈 Please select and upload all your Zammad `.xlsx` files simultaneously to generate the master report.")