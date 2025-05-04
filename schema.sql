-- schema.sql
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
);


CREATE TABLE credit_cards (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    id_number TEXT NOT NULL,
    card_number TEXT NOT NULL,
    valid_date TEXT NOT NULL,
    cvc TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);