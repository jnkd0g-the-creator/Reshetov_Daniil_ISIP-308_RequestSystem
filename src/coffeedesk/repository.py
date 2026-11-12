"""SQL only: caller supplies visibility scope and validated business intent."""

from datetime import datetime, timezone

PUBLIC_USER = "id,username,name,role_code,active"
REQUEST_SELECT = """
SELECT r.*, c.name cafe_name, cat.name category_name, s.name status_name,
       u.name applicant_name, a.name assignee_name
FROM Requests r JOIN Cafes c ON c.id=r.cafe_id
JOIN Categories cat ON cat.id=r.category_id JOIN Statuses s ON s.code=r.status_code
JOIN Users u ON u.id=r.applicant_id LEFT JOIN Users a ON a.id=r.assignee_id
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_dict(row):
    if row is None:
        return None
    result = dict(row)
    result["number"] = f"CB-{result['id']:05d}"
    result["archived"] = bool(result["archived"])
    return result


class Repository:
    def __init__(self, con):
        self.con = con

    def user(self, user_id):
        row = self.con.execute(f"SELECT {PUBLIC_USER} FROM Users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def user_by_username(self, username):
        row = self.con.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None

    def users(self, only_id=None):
        sql = f"SELECT {PUBLIC_USER} FROM Users"
        params = []
        if only_id is not None:
            sql += " WHERE id=?"
            params.append(only_id)
        return [dict(row) for row in self.con.execute(sql + " ORDER BY id", params)]

    def catalog(self, name):
        table, order = {"categories": ("Categories", "id"), "statuses": ("Statuses", "sort_order"), "cafes": ("Cafes", "id")}[name]
        return [dict(row) for row in self.con.execute(f"SELECT * FROM {table} ORDER BY {order}")]

    def exists(self, catalog, value):
        table, key = {"cafe_id": ("Cafes", "id"), "category_id": ("Categories", "id")}[catalog]
        return self.con.execute(f"SELECT 1 FROM {table} WHERE {key}=?", (value,)).fetchone() is not None

    def request(self, request_id):
        return request_dict(self.con.execute(REQUEST_SELECT + " WHERE r.id=?", (request_id,)).fetchone())

    def requests(self, scope=None, q="", status_code=None, category_id=None, cafe_id=None, archived=False, limit=100, offset=0):
        where, values = ["r.archived=?"], [int(archived)]
        if scope:
            field, value = scope
            assert field in ("applicant_id", "assignee_id")
            where.append(f"r.{field}=?")
            values.append(value)
        for field, value in [("status_code", status_code), ("category_id", category_id), ("cafe_id", cafe_id)]:
            if value is not None:
                where.append(f"r.{field}=?")
                values.append(value)
        if q:
            # Treat %, _ and backslash as literals, not user-provided wildcards.
            escaped = q.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where.append("(CASEFOLD(r.title) LIKE ? ESCAPE '\\' OR CASEFOLD(r.description) LIKE ? ESCAPE '\\' OR ('cb-' || printf('%05d',r.id)) LIKE ? ESCAPE '\\' OR CAST(r.id AS TEXT)=?)")
            values.extend([f"%{escaped}%"] * 3 + [q])
        sql = REQUEST_SELECT + " WHERE " + " AND ".join(where) + " ORDER BY r.id DESC LIMIT ? OFFSET ?"
        return [request_dict(row) for row in self.con.execute(sql, [*values, limit, offset])]

    def create_request(self, fields):
        columns = ["title", "description", "cafe_id", "category_id", "applicant_id", "priority"]
        cur = self.con.execute("INSERT INTO Requests(" + ",".join(columns) + ") VALUES(?,?,?,?,?,?)", [fields[key] for key in columns])
        return cur.lastrowid

    def update_request(self, request_id, fields):
        allowed = {"title", "description", "cafe_id", "category_id", "priority", "status_code", "assignee_id", "archived"}
        assert fields and set(fields) <= allowed
        values = dict(fields, updated_at=now())
        self.con.execute("UPDATE Requests SET " + ",".join(f"{key}=?" for key in values) + " WHERE id=?", [*values.values(), request_id])

    def history(self, request_id):
        return [dict(row) for row in self.con.execute("SELECT h.*,u.name actor_name FROM RequestHistory h JOIN Users u ON u.id=h.actor_id WHERE request_id=? ORDER BY h.id", (request_id,))]

    def add_history(self, request_id, actor_id, event, old=None, new=None):
        self.con.execute("INSERT INTO RequestHistory(request_id,actor_id,event,old_value,new_value) VALUES(?,?,?,?,?)", (request_id, actor_id, event, old, new))

    def comments(self, request_id):
        return [dict(row) for row in self.con.execute("SELECT c.*,u.name author_name FROM Comments c JOIN Users u ON u.id=c.author_id WHERE request_id=? ORDER BY c.id", (request_id,))]

    def add_comment(self, request_id, author_id, body):
        cur = self.con.execute("INSERT INTO Comments(request_id,author_id,body) VALUES(?,?,?)", (request_id, author_id, body))
        return next(row for row in self.comments(request_id) if row["id"] == cur.lastrowid)

    def set_password(self, user_id, hashed):
        self.con.execute("UPDATE Users SET password_hash=? WHERE id=?", (hashed, user_id))

    def session(self, hashed):
        row = self.con.execute("SELECT * FROM Sessions WHERE token_hash=?", (hashed,)).fetchone()
        return dict(row) if row else None

    def add_session(self, hashed, csrf_hash, user_id, expires_at, current_time):
        self.con.execute("DELETE FROM Sessions WHERE expires_at<=?", (current_time,))
        self.con.execute("INSERT INTO Sessions(token_hash,csrf_hash,user_id,expires_at) VALUES(?,?,?,?)", (hashed, csrf_hash, user_id, expires_at))

    def delete_session(self, hashed):
        self.con.execute("DELETE FROM Sessions WHERE token_hash=?", (hashed,))
