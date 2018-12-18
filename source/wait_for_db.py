#!/usr/bin/env python

import sys
import pymysql


def wait_for(host, port, user, password, database):
    """wait for mysql init"""
    try:
        db = pymysql.connect(host=host, port=int(port), user=user, password=password, database=database)
        db.close()
        sys.exit(0)
    except pymysql.err.InternalError:
        print('InternalError')
        sys.exit(1)
    except pymysql.err.OperationalError:
        print('OperationalError')
        sys.exit(1)
    except Exception:
        print('Error')
        sys.exit(1)


if __name__ == '__main__':
    host = sys.argv[1]
    port = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    database = sys.argv[5]
    wait_for(host, port, user, password, database)
