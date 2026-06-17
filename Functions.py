import streamlit as st
import sqlite3
import requests
import re

# Create a database of books the user is currently reading
def reading_db(name):
    conn = sqlite3.connect(f"{name}.db")
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

# Add books to the "reading_list" table we created above
def insert_title(title, author, year, page_count, image_url):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reading_list")
    cursor.execute("INSERT OR IGNORE INTO reading_list (title, author, year, page_count, pages_read, image_url) VALUES (?, ?, ?, ?, 0, ?)", (title, author, year, page_count, image_url,))
    conn.commit()
    conn.close()


# Search books online via API
@st.cache_data
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

        image_links = volume_info.get("imageLinks", {})
        image_url = image_links.get("thumbnail", "https://via.placeholder.com/128x192.png?text=No+Cover")

        book_data = {
                "title": volume_info.get('title', 'Unknown title'),
                "author": ",".join(volume_info.get('authors', ['Unknown author'])),
                "year": volume_info.get("publishedDate", "0000")[:4],
                "page_count": volume_info.get("pageCount", 0),
                "image_url": image_url
            }
        formatted_books.append(book_data)
    
    return formatted_books


# Show a list of all books being read right now
def get_all_titles():
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, year, page_count, pages_read, image_url FROM reading_list")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Remove names from the list
def delete_entry(id):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reading_list WHERE id = ?", (id, ))
    conn.commit()
    conn.close()

# Button for updating a field (e.g. page count for a different edition, or format)
# Update entries
def update_name(id, new_name):
    conn = sqlite3.connect("reading.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE reading_list SET title = ? WHERE id = ?", (new_name, id, ))
    conn.commit()
    conn.close()

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