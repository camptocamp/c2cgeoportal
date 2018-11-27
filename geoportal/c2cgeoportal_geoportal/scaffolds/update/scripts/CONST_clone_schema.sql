CREATE OR REPLACE FUNCTION clone_schema(
    source_schema text,
    dest_schema text,
    include_recs boolean)
  RETURNS void AS
$BODY$

-- This function will clone all sequences, tables, data, views & functions from any existing schema to a
-- new one, just call:
-- SELECT clone_schema('current_schema', 'new_schema', TRUE);
-- See also: https://www.postgresql.org/message-id/CANu8FiyJtt-0q%3DbkUxyra66tHi6FFzgU8TqVR2aahseCBDDntA%40mail.gmail.com

DECLARE
  src_oid oid;
  func record;
  args text;
  object text;
  seq record;
  buffer text;
  srctbl text;
  default_ text;
  column_ text;
  qry text;
  dest_qry text;
  v_def text;
  owner text;
  grantor text;
  privilege_type text;
  sq_last_value bigint;
  sq_cycled char(10);

BEGIN

-- Check that source_schema exists
  SELECT oid INTO src_oid
    FROM pg_namespace
   WHERE nspname = quote_ident(source_schema);
  IF NOT FOUND
    THEN
    RAISE EXCEPTION 'source schema % does not exist!', source_schema;
    RETURN;
  END IF;

  -- Check that dest_schema does not yet exist
  PERFORM nspname
    FROM pg_namespace
   WHERE nspname = quote_ident(dest_schema);
  IF FOUND
    THEN
    RAISE EXCEPTION 'dest schema % already exists!', dest_schema;
    RETURN;
  END IF;

  IF quote_ident(dest_schema) != dest_schema
  THEN
     RAISE EXCEPTION 'dest schema % must be a valid identifier!', dest_schema;
    RETURN;
  END IF;

  EXECUTE 'CREATE SCHEMA ' || quote_ident(dest_schema);
  EXECUTE 'SELECT schema_owner
    FROM information_schema.schemata
    WHERE schema_name = ' || quote_literal(source_schema) || ';'
    INTO owner;
  EXECUTE 'ALTER SCHEMA ' || quote_ident(dest_schema) || ' OWNER TO ' || quote_ident(owner);

  -- Create sequences
  -- TODO: Find a way to make this sequence's owner is the correct table.
  FOR seq IN
    SELECT sequence_name::text, start_value, minimum_value, maximum_value, increment, cycle_option
    FROM information_schema.sequences
    WHERE sequence_schema = quote_ident(source_schema)
  LOOP
    EXECUTE 'CREATE SEQUENCE ' || quote_ident(dest_schema) || '.' || quote_ident(seq.sequence_name);
    srctbl := quote_ident(source_schema) || '.' || quote_ident(seq.sequence_name);

    EXECUTE 'SELECT last_value FROM ' || quote_ident(source_schema) || '.' || quote_ident(seq.sequence_name) || ';'
        INTO sq_last_value;

    IF seq.cycle_option = 'YES'
    THEN
      sq_cycled := 'CYCLE';
    ELSE
      sq_cycled := 'NO CYCLE';
    END IF;

    EXECUTE 'ALTER SEQUENCE ' || quote_ident(dest_schema) || '.' || quote_ident(seq.sequence_name)
        || ' INCREMENT BY ' || seq.increment
        || ' MINVALUE ' || seq.minimum_value
        || ' MAXVALUE ' || seq.maximum_value
        || ' START WITH ' || seq.start_value
        || ' RESTART ' || seq.minimum_value
        || sq_cycled || ';';

    buffer := quote_ident(dest_schema) || '.' || quote_ident(seq.sequence_name);
    IF include_recs
    THEN
      EXECUTE 'SELECT setval( ''' || buffer || ''', ' || sq_last_value || ');';
    ELSE
      EXECUTE 'SELECT setval( ''' || buffer || ''', ' || seq.start_value || ');';
    END IF;
  END LOOP;

-- Create tables
  FOR object IN
    SELECT TABLE_NAME::text
    FROM information_schema.tables
    WHERE table_schema = quote_ident(source_schema)
      AND table_type = 'BASE TABLE'
  LOOP
    buffer := quote_ident(dest_schema) || '.' || quote_ident(object);
    EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || quote_ident(source_schema) || '.' || quote_ident(object)
        || ' INCLUDING ALL)';

    EXECUTE 'SELECT tableowner
      FROM pg_catalog.pg_tables
      WHERE schemaname = ' || quote_literal(source_schema) || ' AND tablename = ' || quote_literal(object) || ';'
      INTO owner;
    EXECUTE 'ALTER TABLE ' || quote_ident(dest_schema) || '.' || quote_ident(object) || ' OWNER TO ' || quote_ident(owner);

    FOR grantor, privilege_type IN
      SELECT tp.grantor, tp.privilege_type
      FROM information_schema.table_privileges AS tp
      WHERE table_schema = quote_ident(source_schema) AND table_name = quote_ident(object)
    LOOP
      EXECUTE 'GRANT ' || privilege_type || ' ON TABLE '
          || quote_ident(source_schema) || '.' || quote_ident(object)
          || ' TO ' || quote_ident(grantor);
    END LOOP;

         IF include_recs
      THEN
      -- Insert records from source table
      EXECUTE 'INSERT INTO ' || buffer || ' SELECT * FROM ' ||
          quote_ident(source_schema) || '.' || quote_ident(object) || ';';
    END IF;

    FOR column_, default_ IN
      SELECT column_name::text,
        REPLACE(column_default::text, source_schema, dest_schema)
        FROM information_schema.COLUMNS
        WHERE table_schema = dest_schema
          AND TABLE_NAME = object
          AND column_default LIKE 'nextval(%' || quote_ident(source_schema) || '%::regclass)'
    LOOP
      EXECUTE 'ALTER TABLE ' || buffer || ' ALTER COLUMN ' || column_ || ' SET DEFAULT ' || default_;
    END LOOP;
  END LOOP;

-- add FK constraint
  FOR qry IN
    SELECT 'ALTER TABLE ' || quote_ident(dest_schema) || '.' || quote_ident(rn.relname)
        || ' ADD CONSTRAINT ' || quote_ident(ct.conname) || ' '
        || replace(pg_get_constraintdef(ct.oid),
            ') REFERENCES ' || quote_ident(source_schema) || '.',
            ') REFERENCES ' || quote_ident(dest_schema) || '.') || ';'
    FROM pg_constraint ct
    JOIN pg_class rn ON rn.oid = ct.conrelid
    WHERE connamespace = src_oid
      AND rn.relkind = 'r'
      AND ct.contype = 'f'
    LOOP
      EXECUTE qry;
    END LOOP;

-- Create views
  FOR object IN
    SELECT table_name::text,
        view_definition
    FROM information_schema.views
    WHERE table_schema = quote_ident(source_schema)
  LOOP
    buffer := quote_ident(dest_schema) || '.' || quote_ident(object);
    SELECT view_definition INTO v_def
    FROM information_schema.views
    WHERE table_schema = quote_ident(source_schema)
     AND table_name = quote_ident(object);

    EXECUTE 'CREATE OR REPLACE VIEW ' || buffer || ' AS ' || v_def || ';';

    EXECUTE 'SELECT viewowner
      FROM pg_catalog.pg_views
      WHERE schemaname = ' || quote_literal(source_schema) || ' AND viewname = ' || quote_literal(object) || ';'
    INTO owner;
    EXECUTE 'ALTER SCHEMA ' || quote_ident(dest_schema) || ' OWNER TO ' || quote_ident(owner);
  END LOOP;

-- Create functions
  FOR func IN
    SELECT oid, proname, proowner
    FROM pg_proc
    WHERE pronamespace = src_oid
  LOOP
    SELECT pg_get_functiondef(func.oid) INTO qry;
    SELECT replace(qry, source_schema, dest_schema) INTO dest_qry;
    EXECUTE dest_qry;
    SELECT rolname FROM pg_roles WHERE oid = func.proowner INTO owner;
    SELECT pg_get_function_identity_arguments(func.oid) INTO args;
    EXECUTE 'ALTER FUNCTION ' || quote_ident(dest_schema) || '.' || quote_ident(func.proname) || '(' || args || ') OWNER TO ' || quote_ident(owner);
  END LOOP;

  RETURN;
END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION clone_schema(text, text, boolean)
  OWNER TO postgres;
