/* TFBSDB2 database schema for MySQL */
create database tfbsdb2;
use tfbsdb2;

/* Gene, location and name/id variants */
create table if not exists genes (
  id integer primary key auto_increment,
  entrez_id integer,
  ensembl_id varchar(50),
  description varchar(500),
  chromosome varchar(20),
  start_promoter integer,
  stop_promoter integer,
  tss integer,
  orientation varchar(1)
);

create table if not exists gene_synonyms (
  id integer primary key auto_increment,
  gene_id integer not null references genes,
  name varchar(200) not null,
  synonym_type varchar(30) not null
);

create table if not exists motif_databases (
  id integer primary key auto_increment,
  name varchar(50) not null,
  url varchar(100)
);

create table if not exists motifs (
  id integer primary key auto_increment,
  motif_database_id integer references motif_databases,
  name varchar(50) not null
);

create table if not exists pssms (
  id integer primary key auto_increment,
  motif_id integer not null references motifs,
  row_index integer not null,
  a float not null,
  c float not null,
  g float not null,
  t float not null
);

create table if not exists tf_binding_sites (
  id integer primary key auto_increment,
  gene_id integer not null references genes,
  motif_id integer not null references motifs,
  start integer not null,
  stop integer not null,
  orientation varchar(1) not null,
  p_value float not null,
  match_sequence varchar(200) not null
);

create table if not exists gene_motifs (
  gene_id integer not null references genes,
  motif_id integer not null references motifs
);
