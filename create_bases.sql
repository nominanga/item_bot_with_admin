create table users(
    id integer primary key,
    tg_id varchar(255),
    fullname varchar(255),
    mail_adress text
);

create table items(
    id integer primary key,
    name varchar(255),
    descript text,
    amount integer,
    price integer,
    img text
);


create table item_deliver(
    id integer primary key,
    delivered boolean,
    user_id integer,
    item_id integer,
    foreign key(user_id) references users(id),
    foreign key(item_id) references items(id)
)

