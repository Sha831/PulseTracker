from db.sessions import get_db_session

def test_session():
    gen = get_db_session()
    session = next(gen)
    print("Session created:", session)
    gen.close()
    print("Session closed")

if __name__ == "__main__":
    test_session()