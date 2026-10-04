"""Demo scenarios: one module per shipped item.

Each module exposes SCENARIO {id, kind, title, blurb, beats} plus an
optional seed_db(db_path)->dict that manipulates the fixture DB so the
video shows full functionality (backdated reviews, prior answers).
Beat types: title | chrome | terminal. Total must land 30-60s.
"""
