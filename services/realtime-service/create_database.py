#!/usr/bin/env python3
"""
Script to create the realtimedb database if it doesn't exist.
Run this before running migrations.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = "realtimedb"

# Connect to postgres database (default database)
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres"  # Connect to default postgres database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    
    exists = cursor.fetchone()
    
    if not exists:
        # Create database
        cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"✅ Database '{DB_NAME}' created successfully")
    else:
        print(f"ℹ️  Database '{DB_NAME}' already exists")
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"❌ Error creating database: {e}")
    exit(1)
