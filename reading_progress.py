import streamlit as st
import sqlite3
import requests
import re

# Create a database of books the user is currently reading
def reading_db():
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    # Create different columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        page_count INT,
        pages_read INT,
        year INT,
        image_url TEXT)  
    ''')
    conn.commit()
    conn.close()

reading_db()

# Add books to the "reading_list" table we created above
def insert_title(title, author, year, page_count, image_url):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reading_list")
    cursor.execute("INSERT OR IGNORE INTO reading_list (title, author, year, page_count, pages_read, image_url) VALUES (?, ?, ?, ?, 0, ?)", (title, author, year, page_count, image_url,))
    conn.commit()
    conn.close()

# Search books online via API
def search_book_online(query_og):
    query = query_og.strip()
    if not query:
        return []
    
    api_key = st.secrets["GOOGLE_BOOKS_API_KEY"]

    code_number = re.sub(r'[- ]', '',query)
    is_isbn = (len(code_number) == 10 and (code_number[:9].isdigit() and code_number[9].upper() in ['X', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])) or \
                (len(code_number) == 13 and code_number.isdigit())

    if is_isbn:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{code_number}&key={api_key}"
    else:
        title_search = query.replace(" ", "+")
        url = f"https://www.googleapis.com/books/v1/volumes?q={title_search}&maxResults=5&key={api_key}"
    
    response = requests.get(url)
    formatted_books = []

    if response.status_code == 200:
        books_dict = response.json().get("items", [])[:5]

    for book in books_dict:
        volume_info = book.get("volumeInfo", {})
        title = volume_info.get('title', 'Unknown title')
        authors = ",".join(volume_info.get('authors', ['Unknown author']))
        pub_date = volume_info.get("publishedDate", "0000")
        year = pub_date[:4] if len(pub_date) >= 4 else "0000"
        page_count = volume_info.get("pageCount", 0)

        image_links = volume_info.get("imageLinks", {})
        image_url = image_links.get("thumbnail", "https://via.placeholder.com/128x192.png?text=No+Cover")

        book_string = f"{title} | {authors} | {year} | {page_count} pages || {image_url}"
        
        formatted_books.append(book_string)
    
    return formatted_books


# Show a list of all books being read right now
def get_all_titles():
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, year, page_count, pages_read, image_url FROM reading_list")
    rows = cursor.fetchall()
    conn.close()
    return rows

title_list = get_all_titles()

# Remove names from the list
def delete_entry(id):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reading_list WHERE id = ?", (id, ))
    conn.commit()
    conn.close()
    st.rerun()

# Update entries
def update_name(id, new_name):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE reading_list SET title = ? WHERE id = ?", (new_name, id, ))
    conn.commit()
    conn.close()
    st.rerun()

titles = get_all_titles()
id_list = [row[0] for row in title_list]

# Button for updating a field (e.g. page count for a different edition, or format)

# Search between entries
def search_names(keyword):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM reading_list WHERE title LIKE ?", (f"%{keyword}%",))
    results = cursor.fetchall()
    conn.close()
    return results

def update_progress(book_id, pages_read):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE reading_list SET pages_read = ? WHERE id = ?", (pages_read, book_id))
    conn.commit()
    conn.close()
    st.rerun()

# TODO: make a function for dropbox (titles = get_all_titles, id_list, selected_id = st.selectbox() etc.) menu and conn, cursor = conn.cursor etc. 



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
                    st.success("Progress updated!")
            st.divider()

    # View reading list
    st.title("My shelf")

with tab_add:
    query = st.text_input("What are you looking for?")
    if query.strip():
        books = search_book_online(query)

        if books:
            selected_book = st.selectbox("Select your book", books)
            if st.button("Save"):
                parts = selected_book.split('|')
                title = parts[0].strip()
                author = parts[1].strip()
                year = parts[2].strip()
                page_count = int(parts[3].replace("pages", " ").strip())
                image_url = parts[4].strip()
                insert_title(title, author, year, page_count, image_url)
                st.success(f"'{title} by {author}' added to the reading list!")
        else:
            st.info("No book matching this search")

with tab_manage:
    st.title("Delete a Name")
    id_list = [row[0] for row in title_list]
    book_dict = {row[0]: f"{row[0]}. {row[1]}" for row in title_list}

    selected_id = st.selectbox("Select ID to delete: ", 
                            options=list(book_dict.keys()),
                            format_func=lambda x: book_dict[x])
    if st.button("Delete"):
        delete_entry(selected_id)
        st.success("Deleted succesfully")

    st.title("Search in your list:")
    query = st.text_input("Search:")
    if query:
        results = search_names(query)
        for r in results: 
            st.write(f"{r[0]}. {r[1]}")



        
