from sqlalchemy import create_engine, text

# Path as used inside Docker
DATABASE_PATH = '/app/trades.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH}')

# Try creating a table or inserting and fetching data
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM trades"))
    for row in result:
        print(row)
