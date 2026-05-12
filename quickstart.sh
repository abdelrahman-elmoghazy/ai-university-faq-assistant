#!/bin/bash

# Auth Service Quick Start Script

set -e

echo "================================"
echo "Auth Service - Quick Start Setup"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to auth-service directory
cd "$(dirname "$0")"

echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "✅ Services are running!"
echo ""
echo "📍 Service URLs:"
echo "   Auth Service: http://localhost:5000"
echo "   PostgreSQL: localhost:5432"
echo ""
echo "📋 Available Endpoints:"
echo "   GET  http://localhost:5000/health"
echo "   POST http://localhost:5000/api/auth/register"
echo "   POST http://localhost:5000/api/auth/login"
echo "   POST http://localhost:5000/api/auth/refresh"
echo "   GET  http://localhost:5000/api/auth/me (requires token)"
echo "   POST http://localhost:5000/api/auth/logout (requires token)"
echo "   GET  http://localhost:5000/api/admin/users (admin only)"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Complete API documentation"
echo "   - ARCHITECTURE.md: System architecture"
echo "   - API_TESTING.md: Testing guide with examples"
echo ""
echo "🛑 To stop services: docker-compose down"
echo "🔄 To restart services: docker-compose restart"
echo "📋 To view logs: docker-compose logs -f auth-service"
echo ""
