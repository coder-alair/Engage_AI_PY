from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.automap import automap_base

# Replace this with your database URL
DATABASE_URL = "postgresql://EngageAI-Recruiter_owner:vz5XWIbuKG8L@ep-blue-waterfall-a5mkyfak.us-east-2.aws.neon.tech/EngageAI-Recruiter?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()

# Create a metadata object
metadata = MetaData()

# Reflect the database schema
metadata.reflect(bind=engine)

# Create an inspector
inspector = inspect(engine)

# Function to convert SQL type to Python type
def get_type(column_type):
    import sqlalchemy.types as types
    
    type_map = {
        types.INTEGER: 'Integer',
        types.BIGINT: 'BigInteger',
        types.SMALLINT: 'SmallInteger',
        types.FLOAT: 'Float',
        types.NUMERIC: 'Numeric',
        types.DECIMAL: 'DECIMAL',
        types.VARCHAR: 'String',
        types.CHAR: 'String',
        types.TEXT: 'Text',
        types.BOOLEAN: 'Boolean',
        types.DATE: 'Date',
        types.DATETIME: 'DateTime',
        types.TIMESTAMP: 'TIMESTAMP',
        types.TIME: 'Time',
        types.BINARY: 'LargeBinary',
        types.VARBINARY: 'LargeBinary',
        types.UUID: 'UUID',
        types.JSON: 'JSON',
        types.ARRAY: 'ARRAY',
    }
    
    for sql_type, sa_type in type_map.items():
        if isinstance(column_type, sql_type):
            return sa_type
    return 'String'  # default to String if type is not recognized

# Generate model code
print("from sqlalchemy import Column, Integer, String, ForeignKey")
print("from sqlalchemy.orm import relationship")
print("from sqlalchemy.ext.declarative import declarative_base")
print()
print("Base = declarative_base()")
print()

for table_name in inspector.get_table_names():
    print(f"class {table_name.capitalize()}(Base):")
    print(f"    __tablename__ = '{table_name}'")
    print()
    
    # Get primary key columns
    pk_columns = inspector.get_pk_constraint(table_name)['constrained_columns']
    
    # Get foreign key columns
    fk_columns = {fk['constrained_columns'][0]: fk for fk in inspector.get_foreign_keys(table_name)}
    
    for column in inspector.get_columns(table_name):
        column_name = column['name']
        column_type = get_type(column['type'])
        nullable = column['nullable']
        
        print(f"    {column_name} = Column({column_type}", end="")
        
        if column_name in pk_columns:
            print(", primary_key=True", end="")
        if not nullable:
            print(", nullable=False", end="")
        if column_name in fk_columns:
            fk = fk_columns[column_name]
            print(f", ForeignKey('{fk['referred_table']}.{fk['referred_columns'][0]}')", end="")
        
        print(")")
    
    # Add relationships
    for fk in inspector.get_foreign_keys(table_name):
        referred_table = fk['referred_table']
        print(f"    {referred_table.lower()} = relationship('{referred_table.capitalize()}')")
    
    print()