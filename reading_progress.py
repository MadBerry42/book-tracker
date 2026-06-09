import streamlit as st
import sqlite3
import requests
import re

st.title("Reading progress")

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
        year INT)  
    ''')
    conn.commit()
    conn.close()

reading_db()

# Add books to the "reading_list" table we created above
def insert_title(title, author, year, page_count):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reading_list")
    count = cursor.fetchone()[0]
    
    cursor.execute("INSERT OR IGNORE INTO reading_list (title, author, year, page_count, pages_read) VALUES (?, ?, ?, ?, 0)", (title, author, year, page_count))
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

        book_string = f"{title} | {authors} | {year} | {page_count} pages"
        
        formatted_books.append(book_string)
    
    return formatted_books

query = st.text_input("What book are you looking for?")
if query.strip():
    books = search_book_online(query)

    if books:
        selected_book = st.selectbox("Select your book", books)
        if st.button("Save"):
            parts = selected_book.split('|')
            title = parts[0]
            author = parts[1]
            year = parts[2]
            page_count = parts[3]
            insert_title(title, author, year, page_count)
            st.success(f"'{title} by {author}' added to the reading list!")
    else:
        st.info("No book matching this search")


# Show a list of all books being read right now
def get_all_titles():
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, year, page_count, pages_read FROM reading_list")
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

st.title("Delete a Name")
id_list = [row[0] for row in title_list]
book_dict = {row[0]: f"{row[0]}. {row[1]}" for row in title_list}

selected_id = st.selectbox("Select ID to delete: ", 
                           options=list(book_dict.keys()),
                           format_func=lambda x: book_dict[x])
if st.button("Delete"):
    delete_entry(selected_id)
    st.success("Deleted succesfully")

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

st.title("Search in your list:")
query = st.text_input("Search:")
if query:
    results = search_names(query)
    for r in results: 
        st.write(f"{r[0]}. {r[1]}")

# View reading list
st.title("View list")
title_list = get_all_titles()
if title_list:
    for indice, row in enumerate(title_list, start=1): 
        st.write(f"**{indice}.** {row[1]}")


# TODO: make a function for dropbox (titles = get_all_titles, id_list, selected_id = st.selectbox() etc.) menu and conn, cursor = conn.cursor etc. 
# Add a progress bar: when button "Pages" is pressed, insert number of pages from the user (or percentage, choose from a dropbox menu),
# Compute progress from n.pages data from the API and show it)


