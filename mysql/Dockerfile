# mysql/Dockerfile
FROM mysql:8.0-debian

COPY conf.d/my.cnf /etc/mysql/conf.d/my.cnf

# 日本語環境を追加
RUN apt-get update && apt-get install -y locales \
    && sed -i -e 's/# \(ja_JP.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=ja_JP.UTF-8

ENV LANG=ja_JP.UTF-8

CMD ["mysqld"]