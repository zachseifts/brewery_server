drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  created timestamp default current_timestamp,
  temp integer not null,
  key text not null
);
