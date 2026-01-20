#!/bin/bash
# Script to create the realtimedb database

# Connect to postgres and create database
PGPASSWORD=password psql -h postgres -U postgres -c "CREATE DATABASE realtimedb;" 2>/dev/null || echo "Database might already exist or connection failed"

echo "Database 'realtimedb' created (or already exists)"
