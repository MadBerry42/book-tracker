from Functions import get_all_titles, search_book_online, insert_title, update_progress, delete_entry, search_names, reading_db
import streamlit as st

# Create database 
reading_db("reading_list")
# ------------------------------------------ UI: TABS -----------------------------------------------
tab_reading_now, tab_add, tab_manage = st.tabs(["Currently reading", "New book", "Manage bookshelf"])

with tab_reading_now:
    books = get_all_titles()
    if books:
        for row in books:
            book_id = row[0]
            title = row[1]
            author = row[2]
            total_pages = row[4] if row[4] > 0 else 100
            pages_already_read = row[5]
            cover_url = row[6]

            if not cover_url or not str(cover_url).startswith("http"):
                cover_url = "https://via.placeholder.com/128x192.png?text=No+Cover"

            col_img, col_txt = st.columns([1, 5])
            with col_img:
                st.image(cover_url, width=70)
            with col_txt:
                st.markdown(f"{title} by {author}")
                current_pages = st.number_input(
                    f"Insert page: ", 
                    min_value=0, 
                    max_value=total_pages, 
                    value=pages_already_read,
                    key=f"input_{book_id}" 
                )

                progress_percent = int((current_pages/total_pages) * 100)
                st.progress(progress_percent / 100)
                st.caption(f"{progress_percent}%")

                if st.button("Save", key=f"btn_save_{book_id}", type="primary"):
                    update_progress(book_id, current_pages)
                    st.rerun()
            st.divider()

with tab_add:
    query = st.text_input("What are you looking for?")
    if query.strip():
        books = search_book_online(query)

        if books:
            selected_book = st.selectbox("Select your book", books, format_func=lambda b: f"{b['title']} - {b['author']} ({b['year']})")
            if st.button("Save"):
                title = selected_book["title"]
                author = selected_book["author"] 
                year = selected_book["year"]
                page_count = selected_book["page_count"] 
                image_url = selected_book["image_url"] 
                insert_title(title, author, year, page_count, image_url)
                st.rerun()
        else:
            st.info("No book matching this search")

with tab_manage:
    title_list = get_all_titles()
    st.title("Delete a Name")
    id_list = [row[0] for row in title_list]
    book_dict = {row[0]: f"{row[1]}" for row in title_list}

    selected_id = st.selectbox("Select ID to delete: ", 
                            options=list(book_dict.keys()),
                            format_func=lambda x: book_dict[x])
    if st.button("Delete"):
        delete_entry(selected_id)
        st.rerun()

    st.title("Search in your list:")
    query = st.text_input("Search:")
    if query:
        results = search_names(query)
        for r in results: 
            st.write(f"{r[1]}")
    


        
