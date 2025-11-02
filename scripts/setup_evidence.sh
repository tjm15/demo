#!/bin/bash
# Evidence Base Setup Script

set -e

echo "🗄️  Setting up Evidence Base..."

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Database connection details
DB_NAME="${DB_NAME:-tpa}"
DB_USER="${DB_USER:-tpa}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"

echo "📊 Applying evidence schema to database $DB_NAME..."

# Apply the evidence schema
PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f scripts/evidence_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Evidence schema applied successfully!"
else
    echo "❌ Failed to apply evidence schema"
    exit 1
fi

# Verify tables were created
echo ""
echo "🔍 Verifying evidence tables..."
TABLES=$(PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'evidence%' ORDER BY table_name;")

if [ -z "$TABLES" ]; then
    echo "❌ No evidence tables found!"
    exit 1
fi

echo "Evidence tables created:"
echo "$TABLES" | while read -r table; do
    if [ -n "$table" ]; then
        echo "  ✓ $table"
    fi
done

echo ""
echo "✅ Evidence Base setup complete!"
echo ""
echo "Next steps:"
echo "  1. Restart the kernel: cd apps/kernel && uvicorn main:app --reload --port 8081"
echo "  2. Restart the frontend: cd website && pnpm run dev"
echo "  3. Navigate to Evidence module in the UI"
echo "  4. Try 'Show housing evidence' or click 'Add Evidence Item'"
