# Optional fallback: if mysqlclient cannot be installed (common on Windows),
# install PyMySQL (pip install pymysql cryptography) and it is used automatically.
try:
    import MySQLdb  # noqa: F401  (mysqlclient)
except ImportError:
    try:
        import pymysql
        pymysql.version_info = (2, 2, 1, "final", 0)
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
