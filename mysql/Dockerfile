FROM mysql:5.7
MAINTAINER kyu yukun@eager.live

ENV AUTO_RUN_DIR=/docker-entrypoint-initdb.d \
    INSTALL_DB_SQL=init_database.sql

COPY ./$INSTALL_DB_SQL $AUTO_RUN_DIR/
RUN chmod a+x $AUTO_RUN_DIR/$INSTALL_DB_SQL
