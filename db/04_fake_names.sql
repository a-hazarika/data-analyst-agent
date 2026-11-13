-- Invented names for customers and sellers. Olist is anonymized, so these are NOT real people or businesses.
-- Run after 02_load.sql (or 03_seed_test.sql). Safe to run again: the same id always gets the same name.
-- Run: docker compose exec -T db psql -U postgres -d analyst -v ON_ERROR_STOP=1 -f /db/04_fake_names.sql
-- No foreign keys on purpose: 02_load.sql and 03_seed_test.sql TRUNCATE the tables these would point at.
BEGIN;

CREATE TABLE IF NOT EXISTS raw.customer_names (
  customer_unique_id  text PRIMARY KEY,   -- one row per person, not per order
  customer_name       text NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.seller_names (
  seller_id    text PRIMARY KEY,
  seller_name  text NOT NULL
);

TRUNCATE raw.customer_names, raw.seller_names;

-- Picks an array element from 8 hex digits of md5(id), starting at position pos.
CREATE OR REPLACE FUNCTION pg_temp.pick(id text, pos int, items text[]) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT items[1 + (('x' || substr(md5(id), pos, 8))::bit(32)::bigint % cardinality(items))]
$$;

WITH lists AS (
  SELECT
    ARRAY['Ana','Bruno','Camila','Daniel','Eduarda','Felipe','Gabriela','Henrique','Isabela','João',
          'Larissa','Marcelo','Natália','Otávio','Patrícia','Rafael','Sabrina','Thiago','Vanessa','William',
          'Aline','Caio','Débora','Emerson','Fernanda','Gustavo','Helena','Igor','Juliana','Leonardo',
          'Mariana','Nelson','Olívia','Paulo','Renata','Sérgio','Tatiane','Vinícius','Yasmin','Diego'] AS firsts,
    ARRAY['Silva','Santos','Oliveira','Souza','Rodrigues','Ferreira','Alves','Pereira','Lima','Gomes',
          'Costa','Ribeiro','Martins','Carvalho','Almeida','Lopes','Soares','Fernandes','Vieira','Barbosa',
          'Rocha','Dias','Nascimento','Andrade','Moreira','Nunes','Marques','Machado','Mendes','Freitas',
          'Cardoso','Ramos','Gonçalves','Santana','Teixeira','Araújo','Pinto','Correia','Batista','Campos'] AS lasts
)
INSERT INTO raw.customer_names
SELECT c.customer_unique_id,
       pg_temp.pick(c.customer_unique_id, 1, firsts) || ' ' ||
       pg_temp.pick(c.customer_unique_id, 9, lasts)  || ' ' ||
       pg_temp.pick(c.customer_unique_id, 17, lasts)
FROM (SELECT DISTINCT customer_unique_id FROM raw.olist_customers) c, lists;

WITH lists AS (
  SELECT
    ARRAY['Casa','Loja','Empório','Mercado','Armazém','Bazar','Depósito','Galeria','Oficina','Mundo',
          'Ponto','Central','Estação','Canto','Império','Rei','Planeta','Feira','Vila','Porto'] AS kinds,
    ARRAY['Aurora','Ipê','Jacarandá','Sabiá','Tucano','Arara','Bem-Te-Vi','Girassol','Pitanga','Jabuticaba',
          'Maracujá','Caju','Açaí','Guará','Tatu','Onça','Beija-Flor','Coqueiro','Buriti','Jatobá',
          'Serra','Litoral','Sertão','Cerrado','Pantanal','Mantiqueira','Ipanema','Paraná','Tietê','Araguaia',
          'Sol','Lua','Estrela','Brisa','Maré','Horizonte','Vale','Campo','Pedra','Rio'] AS names,
    ARRAY['Comércio','Variedades','Distribuidora','Importados','Online','Store','Shop','Magazine','Express','Atacado'] AS suffixes
)
INSERT INTO raw.seller_names
SELECT s.seller_id,
       pg_temp.pick(s.seller_id, 1, kinds) || ' ' ||
       pg_temp.pick(s.seller_id, 9, names) || ' ' ||
       pg_temp.pick(s.seller_id, 17, suffixes)
FROM raw.olist_sellers s, lists;

COMMIT;
ANALYZE raw.customer_names, raw.seller_names;

SELECT 'customer_names' AS table_name, count(*) AS total, count(DISTINCT customer_name) AS distinct_names FROM raw.customer_names
UNION ALL
SELECT 'seller_names', count(*), count(DISTINCT seller_name) FROM raw.seller_names;
