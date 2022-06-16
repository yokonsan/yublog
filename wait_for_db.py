import sys
import pymysql


def wait_for(config):
    """wait for mysql init"""
    code = 0
    try:
        db = pymysql.connect(**config)
        db.close()
    except pymysql.err.InternalError:
        print("InternalError")
        code = 1
    except pymysql.err.OperationalError:
        print("OperationalError")
        code = 1
    finally:
        sys.exit(code)


if __name__ == '__main__':
    wait_for({
        "host": sys.argv[1],
        "port": int(sys.argv[2]),
        "user": sys.argv[3],
        "password": sys.argv[4],
        "database": sys.argv[5]
    })
