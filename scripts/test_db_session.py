from db.sessions import get_db_session

"""
Disclamer : 
-Please dont refer these test scripts for general testing as these were made during specific cases/time during designing backend
"""

def test_session():
    gen = get_db_session()
    session = next(gen)
    print("Session created:", session)
    gen.close()
    print("Session closed")

if __name__ == "__main__":
    test_session()