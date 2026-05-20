-- users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- books
CREATE TABLE books (
    work_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    isbn10 TEXT,
    isbn13 TEXT,
    average_rating REAL,
    rating_update_date DATE,
    rating_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- authors
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- a book's author(s)
CREATE TABLE book_authors (
    work_id TEXT,
    author_id INTEGER,
    PRIMARY KEY (work_id, author_id),
    FOREIGN KEY (work_id) REFERENCES books(work_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);

-- indexing to make queries more efficient
CREATE INDEX idx_book_authors_work ON book_authors(work_id);
CREATE INDEX idx_book_authors_author ON book_authors(author_id);

-- subjects
CREATE TABLE subjects (
    subject_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- a book's subjects
CREATE TABLE book_subjects (
    work_id TEXT,
    subject_id INTEGER,
    PRIMARY KEY (work_id, subject_id),
    FOREIGN KEY (work_id) REFERENCES books(work_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);

-- indexing to make queries more efficient
CREATE INDEX idx_book_subjects_work ON book_subjects(work_id);
CREATE INDEX idx_book_subjects_subject ON book_subjects(subject_id);

-- bookshelf -> a user's books
CREATE TABLE user_bookshelf (
    user_id INTEGER,
    work_id TEXT,
    rating INTEGER,
    review TEXT,
    date_added DATE,
    read_count INTEGER,
    shelf TEXT,
    PRIMARY KEY (user_id, work_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES books(work_id) ON DELETE CASCADE
);

-- indexing to make queries more efficient
CREATE INDEX idx_user_books_user ON user_books(user_id);
CREATE INDEX idx_user_books_work ON user_books(work_id);

-- book embeddings
CREATE TABLE book_embeddings (
    work_id TEXT PRIMARY KEY,
    embedding BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES books(work_id) ON DELETE CASCADE
);

-- user embeddings
CREATE TABLE user_embeddings (
    user_id INTEGER PRIMARY KEY,
    embedding BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- book similarity graph
CREATE TABLE book_similarity (
    work_id_1 TEXT,
    work_id_2 TEXT,
    similarity_score REAL,
    PRIMARY KEY (work_id_1, work_id_2),
    FOREIGN KEY (work_id_1) REFERENCES books(work_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id_2) REFERENCES books(work_id) ON DELETE CASCADE,
    CHECK (work_id_1 < work_id_2)
);

-- user similarity graph
CREATE TABLE user_similarity (
    user_id_1 INTEGER,
    user_id_2 INTEGER,
    similarity_score REAL,
    PRIMARY KEY (user_id_1, user_id_2),
    FOREIGN KEY (user_id_1) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id_2) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK (user_id_1 < user_id_2)
);

-- book match score for a user (one to many)
CREATE TABLE matches (
    user_id INTEGER,
    work_id INTEGER,
    match_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    PRIMARY KEY (user_id, work_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES books(work_id) ON DELETE CASCADE
);

-- indexing to make queries more efficient
CREATE INDEX idx_user_matches ON user_book_matches(user_id);
CREATE INDEX idx_work_matches ON user_book_matches(work_id);
CREATE INDEX idx_match_score ON user_book_matches(match_score DESC);